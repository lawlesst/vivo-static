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

#Setup the VIVO store
store = VIVOUpdateStore(email, password)
store.open((read, update))

# vivo data set
vds = Dataset(store=store)
vds.namespace_manager = ns_mgr


def get_people():
    rq = """
    construct {
        ?p a tmp:Person ;
            rdfs:label ?name ;
            tmp:pic ?picture ;
            tmp:description ?description ;
            tmp:position ?position .
        ?position rdfs:label ?title ;
            tmp:org ?org.
        ?org rdfs:label ?orgName .
    }
    where {
            ?p a foaf:Person ;
                rdfs:label ?name .
            OPTIONAL { ?p wos:description ?description }
            OPTIONAL { ?p wos:photo ?picture }
            OPTIONAL {
                ?f vivo:relatedBy ?position .
                ?position a vivo:Position ;
                    rdfs:label ?title ;
                    vivo:relates ?org .
                ?org a foaf:Organization ;
                     rdfs:label ?orgName .
            }
            FILTER REGEX(?name, ?startswith, "i")
    }
    LIMIT 10
    """
    rq = """
    select ?p ?name ?ln
    where {
        ?p a foaf:Person ;
           rdfs:label ?name .
        BIND(STRAFTER(str(?p), "http://vivo.school.edu/individual/") as ?ln)
    }
    ORDER BY ?name
    LIMIT 50
    """
    #rsp = vds.query(rq.replace("?startswith", "\"^a\""))
    #print rsp.graph.serialize(format="turtle")
    out = [dict(name=r.name, uri=r.p, local=r.ln) for r in vds.query(rq)]
    return out


def get_person(pid):
    uri = D[pid]
    rq = """
        select ?name ?description ?picture ?overview ?orcid
        where {
            ?p a foaf:Person ;
                    rdfs:label ?name .
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

def _gv(row, key):
    v = getattr(row, key)
    if v is not None:
        return v.toPython()
    else:
        return None

def get_pubs(pid):
    uri = D[pid]
    rq = """
    select ?pub ?title ?date ?authorList ?doi ?pmid ?venue
    where {
        ?aship a vivo:Authorship ;
            vivo:relates ?person, ?pub .
        ?pub a bibo:Document ;
            rdfs:label ?title ;
            wos:authorList ?authorList ;
            vivo:dateTimeValue ?dtv .
        ?dtv rdfs:label ?date .
        OPTIONAL {
            ?pub vivo:hasPublicationVenue ?pv .
            ?pv rdfs:label ?venue .
        }
        OPTIONAL { ?pub bibo:doi ?doi }
        OPTIONAL { ?pub bibo:pmid ?pmid }
    }
    ORDER BY DESC(?date)
    """
    rsp = vds.query(rq, initBindings={'person': uri})
    pubs = [
        dict(
            title=r.title.toPython(),
            authors=r.authorList.toPython(),
            date=r.date.toPython(),
            doi=_gv(r, 'doi'),
            pmid=_gv(r, 'pmid'),
            venue=_gv(r, 'venue'),
            year=int(r.date[:4])
        ) for r in rsp
    ]
    return pubs
