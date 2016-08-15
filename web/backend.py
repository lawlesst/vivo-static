""""
This is the data access layer.

Queries are run to fetch data from the VIVO store and converted
to Python data structures - lists and dictionaries - that are then
passed off to the templates.
"""


import os

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.query import ResultException
from rdflib.compare import graph_diff

from vstore import VIVOUpdateStore
from rdflib.namespace import SKOS, RDF, RDFS
from rdflib.graph import Dataset

#from namespaces import rq_prefixes, VIVO
from namespaces import ns_mgr, D

import logging

# vivo credentials
email = os.environ['VIVO_EMAIL']
password = os.environ['VIVO_PASSWORD']
read = os.environ['VIVO_URL'] + '/api/sparqlQuery'
update = os.environ['VIVO_URL'] + '/api/sparqlUpdate'

DATA_NAMESPACE = os.environ['DATA_NAMESPACE']

from namespaces import FOAF, TMP, VIVO

#Setup the VIVO store
store = VIVOUpdateStore(email, password)
store.open((read, update))

# vivo data set
vds = Dataset(store=store)
vds.namespace_manager = ns_mgr


class Profile(object):
    """
    Build a temporary RDF model of the profile.
    Use additional SPARQL select queries to find attributes we
    are interested in.
    """

    def __init__(self, local_name):
        self.local_name = local_name
        self.uri = D[local_name]
        self.model = self._generate_model()
        self.model.namespace_manager = ns_mgr

    def _generate_model(self):
        rq = """
        CONSTRUCT {
              ?person a foaf:Person ;
                rdfs:label ?name ;
                foaf:firstName ?first ;
                foaf:lastName ?last ;
                vivo:middleName ?middle ;
                tmp:orcid ?orcid ;
                vivo:overview ?overview ;
                foaf:thumbnail ?picture ;
                tmp:hasWebsite ?vcUrl .
              # websites
              ?vcUrl rdfs:label ?websiteLabel ;
                     tmp:url ?website .
              # publications
              ?aship a vivo:Authorship ;
                    vivo:relates ?person, ?pub .
              ?pub a bibo:Document ;
                rdfs:label ?title ;
                vivo:dateTimeValue ?dtv ;
                wos:authorList ?authorList ;
                bibo:doi ?doi ;
                bibo:pmid ?pmid ;
                vivo:hasPublicationVenue ?pv .
              ?pv rdfs:label ?venueName .
              ?dtv vivo:dateTime ?date .
              # positions
              ?pos a vivo:Position ;
                    vivo:relates ?person ;
                    rdfs:label ?title ;
                    tmp:positionOrg ?orgName ;
                    tmp:start ?startDate ;
                    tmp:end ?endDate .
            }
            WHERE {
              {
                # person details
                ?person a foaf:Person ;
                        rdfs:label ?name ;

                OPTIONAL { ?person foaf:firstName ?first }
                OPTIONAL { ?person foaf:lastName ?last }
                OPTIONAL { ?person vivo:orcidId ?orcidIri }
                OPTIONAL { ?person vivo:middleName ?middle }
                OPTIONAL { ?person foaf:thumbnail ?picture }
                OPTIONAL { ?person vivo:overview ?overview }
                BIND(strafter(str(?orcidIri), ".org/") AS ?orcid)
              }
              # websites
              UNION {
                ?person obo:ARG_2000028 ?vci .
                ?vci vcard:hasURL ?vcUrl .
                ?vcUrl vcard:url ?website .
                OPTIONAL {?vcUrl rdfs:label ?websiteLabel }
              }
              # pubs
              UNION {
                ?person a foaf:Person .
                   ?aship a vivo:Authorship ;
                        vivo:relates ?person, ?pub .
                    ?pub a bibo:Document ;
                        rdfs:label ?title ;
                        vivo:dateTimeValue ?dtv .
                    ?dtv vivo:dateTime ?date .
                    OPTIONAL {
                        ?pub vivo:hasPublicationVenue ?pv .
                        ?pv rdfs:label ?venueName .
                    }
                    OPTIONAL { ?pub bibo:doi ?doi }
                    OPTIONAL { ?pub bibo:pmid ?pmid }
                    OPTIONAL { ?pub wos:authorList ?authorList }
              }
              # positions
              UNION {
                  ?pos a vivo:Position ;
                       rdfs:label ?title ;
                       vivo:relates ?person, ?org .
                  ?org a foaf:Organization ;
                       rdfs:label ?orgName .
                  OPTIONAL {
                    ?pos vivo:dateTimeInterval ?dti .
                    ?dti vivo:start ?start .
                    ?start vivo:dateTime ?startDate .
                  }
                  OPTIONAL {
                    ?pos vivo:dateTimeInterval ?dti .
                    ?dti vivo:end ?end .
                    ?end vivo:dateTime ?endDate .
                  }
              }
            }
        """
        g = vds.query(rq, initBindings=dict(person=self.uri)).graph
        return g

    def _gv(self, predicate):
        v = self.model.value(subject=self.uri, predicate=predicate)
        return v

    def profile(self):
        return {
            'name': self._gv(RDFS.label),
            'first': self._gv(FOAF.firstName),
            'last': self._gv(FOAF.lastName),
            'orcid': self._gv(TMP.orcid),
            'overview': self._gv(VIVO.overview),
            'picture': self._gv(FOAF.thumbnail)
        }

    def websites(self):
        rq = """
        select ?label ?url
        where {
            ?person tmp:hasWebsite ?ws .
            ?ws tmp:url ?url .
            OPTIONAL { ?ws rdfs:label ?label }
        }
        ORDER BY ?label
        """
        rsp = self.model.query(rq, initBindings={'person': self.uri})
        out = []
        for row in rsp:
            url = row.url.toPython()
            label = _gv(row, "label")
            if label is None:
                label = url
            out.append(dict(url=url, label=label))
        return out

    def _date_value(self, value, year=False):
        if value is None:
            return
        dstring = str(value.toPython())
        if year is True:
            return dstring[:4]
        else:
            return dstring[:10]

    def publications(self):
        rq = """
        select ?pub ?title ?date ?authorList ?doi ?pmid ?venue
        where {
            ?aship a vivo:Authorship ;
                vivo:relates ?person, ?pub .
            ?pub a bibo:Document ;
                rdfs:label ?title ;
                vivo:dateTimeValue ?dtv .
            ?dtv vivo:dateTime ?date .
            OPTIONAL {
                ?pub vivo:hasPublicationVenue ?pv .
                ?pv rdfs:label ?venue .
            }
            OPTIONAL { ?pub bibo:doi ?doi }
            OPTIONAL { ?pub bibo:pmid ?pmid }
            OPTIONAL { ?pub wos:authorList ?authorList }
        }
        """
        rsp = self.model.query(rq, initBindings={'person': self.uri})
        pubs = [
            dict(
                title=r.title.toPython(),
                authors=_gv(r, 'authorList'),
                date=self._date_value(r.date),
                doi=_gv(r, 'doi'),
                pmid=_gv(r, 'pmid'),
                venue=_gv(r, 'venue'),
                year=self._date_value(r.date, year=True)
            ) for r in rsp
        ]
        # hack to avoid duplicate results from SPARQL query
        # http://stackoverflow.com/a/9427216
        return [dict(t) for t in set([tuple(d.items()) for d in pubs])]

    def positions(self):
        rq = """
        select ?pos ?title ?orgName ?startDate ?endDate
        where {
          ?pos a vivo:Position ;
               rdfs:label ?title ;
               vivo:relates ?person ;
               tmp:positionOrg ?orgName .
           OPTIONAL {
            ?pos tmp:start ?startDate .
           }
           OPTIONAL {
            ?pos tmp:end ?endDate .
           }
        }
        """
        rsp = self.model.query(rq, initBindings={'person': self.uri})
        positions = []
        for r in rsp:
            positions.append(
                dict(
                    title=r.title,
                    org=r.orgName,
                    start=self._date_value(r.startDate, year=True),
                    end = self._date_value(r.endDate, year=True),
                )
            )
        return positions

    def schema_org(self):
        """
        Schema.org representation of the profile.
        """
        rq = u"""
        CONSTRUCT {
            ?person a schema:Person ;
                schema:name ?name ;
                schema:image ?picture ;
                schema:sameAs ?orcidUrl .
        }
        WHERE {
            ?person a foaf:Person ;
                rdfs:label ?name .
            OPTIONAL { ?person foaf:thumbnail ?picture }
            OPTIONAL { ?person tmp:orcid ?orcid }
            BIND(IRI(CONCAT("http://orcid.org/", ?orcid)) as ?orcidUrl)
        }
        """
        g = Graph()
        g += self.model.query(rq, initBindings={'person': self.uri}).graph

        # Get pubs
        pub_rq = """
        CONSTRUCT {
            ?pub a schema:ScholarlyArticle ;
                schema:name ?title ;
                schema:sameAs ?doiUrl ;
                schema:author ?person .
        }
        WHERE {
            ?aship a vivo:Authorship .
            ?aship vivo:relates ?person, ?pub .
            ?pub a bibo:Document ;
                rdfs:label ?title ;
                bibo:doi ?doi .
            BIND(IRI(CONCAT("http://dx.doi.org/", ?doi)) as ?doiUrl)
        }
        """
        g += self.model.query(pub_rq, initBindings={'person':self.uri}).graph
        #print g.serialize(format="turtle")
        jsonld = g.serialize(format="json-ld", context="http://schema.org", indent=2)
        try:
            return jsonld.encode('utf-8', 'ignore')
        except:
            return None

def _gv(row, key):
    """
    Helper to get value from a SPARQL result row.
    """
    v = getattr(row, key)
    if v is not None:
        return v.toPython()
    else:
        return None


def get_people():
    """
    Get all the people with publications in the VIVO system.
    """
    rq = """
    select distinct ?p ?name ?ln ?picture
    where {
        ?aship a vivo:Authorship ;
            vivo:relates ?p, ?pub .
        ?pub a bibo:Document .
        ?p a foaf:Person ;
           rdfs:label ?name .
        BIND(STRAFTER(str(?p), "individual/") as ?ln)
        OPTIONAL {
               ?p a foaf:Person .
               ?p foaf:thumbnail ?picture
         }
    }
    ORDER BY ?name
    """
    out = [
        dict(
            name=r.name,
            uri=r.p,
            local=r.ln,
            picture=r.picture,
            nidx=r.name.toPython()[0].lower()
        )
        for r in vds.query(rq)]
    return out


if __name__ == '__main__':
    import sys
    p = Profile(sys.argv[1])
    p.schema_org()
