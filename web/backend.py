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
from rdflib.namespace import SKOS, RDF
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

#Setup the VIVO store
store = VIVOUpdateStore(email, password)
store.open((read, update))

# vivo data set
vds = Dataset(store=store)
vds.namespace_manager = ns_mgr


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
        ?p a foaf:Person ;
           rdfs:label ?name .
           #vivo:relatedBy ?aship .
        #?aship a vivo:Authorship .
        BIND(STRAFTER(str(?p), "--dns--") as ?ln)
        OPTIONAL { ?p wos:photo ?picture }
    }
    ORDER BY ?name
    #ORDER BY RAND()
    #LIMIT 75
    """.replace("--dns--", D)
    #rsp = vds.query(rq.replace("?startswith", "\"^a\""))
    #print rsp.graph.serialize(format="turtle")
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


def get_person(pid):
    """
    Get person profile information.
    """
    uri = D[pid]
    rq = """
        select ?name ?description ?picture ?overview ?orcid
        where {
            ?p a foaf:Person ;
                    rdfs:label ?name ;
                    vivo:orcidId ?orcid .
            OPTIONAL { ?p wos:description ?description }
            OPTIONAL { ?p wos:photo ?picture }
            OPTIONAL { ?p wos:orcid ?orcid }
            OPTIONAL { ?p vivo:overview ?overview }
        }
    """
    rsp = vds.query(rq, initBindings={'p': uri})
    vdata = [r for r in rsp][0]
    return dict(
        name=vdata.name,
        description=vdata.description,
        orcid=vdata.orcid,
        picture=vdata.picture,
        overview=vdata.overview,
    )


def get_pubs(pid):
    """
    Get publications for a person.
    """
    uri = D[pid]
    rq = """
    select ?pub ?title ?date ?year ?authorList ?doi ?pmid ?venue
    where {
        ?aship a vivo:Authorship ;
            vivo:relates ?person, ?pub .
        ?pub a obo:IAO_0000030 ;
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
        BIND( year(?date) as ?year )
    }
    #ORDER BY DESC(?date)
    #LIMIT 10
    """
    rsp = vds.query(rq, initBindings={'person': uri})
    pubs = [
        dict(
            title=r.title.toPython(),
            authors=_gv(r, 'authorList'),
            date=r.date.toPython()[:10],
            doi=_gv(r, 'doi'),
            pmid=_gv(r, 'pmid'),
            venue=_gv(r, 'venue'),
            year=r.date.toPython()[:4]
        ) for r in rsp
    ]
    return pubs
