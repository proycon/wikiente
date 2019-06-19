#!/usr/bin/env python3

# Maarten van Gompel (proycon)
# Centre for Language and Speech Technology
# Radboud University Nijmegen
# GNU Public License v3

import sys
import os.path
import argparse
import spotlight
import folia.main as folia
from requests.exceptions import HTTPError
from wikiente import VERSION

METRIC_SET = "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/spotlight/metrics.foliaset.ttl"
ENTITYSET_MODE_1 = "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/spotlight/dbpedia.foliaset.ttl"
ENTITYSET_MODE_2 = "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/namedentities.foliaset.ttl"
RELATIONSET = "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/babelente.relations.ttl" #same as babelente

def getclass(types):
    if 'DBpedia:Place' in types or 'DBpedia:Location' in types:
        return "loc"
    if 'DBpedia:Person' in types:
        return "per"
    if 'DBpedia:Event' in types:
        return "eve"
    if 'DBpedia:Product' in types:
        return "prod"
    if 'DBpedia:Time' in types:
        return "time"
    if 'DBpedia:Organization' in types:
        return "org"
    return None

def getlanguage(element):
    try:
        return element.annotation(folia.LangAnnotation)
    except folia.NoSuchAnnotation:
        if element.parent:
            return getlanguage(element.parent)
        else:
            return None

def process(file, **kwargs):
    selectlang = kwargs.get('language',None)
    doc = folia.Document(file=file, processor=folia.Processor.create("wikiente",version=VERSION))
    if not doc.declared(folia.Sentence):
        print("ERROR: Document contains no sentence annotation, but this is required for wikiente",file=sys.stderr)
        sys.exit(2)
    for sentence in doc.sentences():
        if kwargs.get('debug') and sentence.id:
            print("Processing sentence ", sentence.id,file=sys.stderr)
        if selectlang:
            foundlang = getlanguage(sentence)
            if foundlang is None:
                print("(no language information, skipping sentence ", repr(sentence),")",file=sys.stderr)
                continue
            elif foundlang.cls != selectlang:
                print("(skipping, language doesn't match, expected ",selectlang," found ", foundlang.cls, file=sys.stderr)
                continue
        text = sentence.text(retaintokenisation=True)
        if kwargs.get('debug'):
            print("Processing: ", text,file=sys.stderr)
        try:
            entities = spotlight.annotate(os.path.join(kwargs.get('server'),"annotate"), text, confidence=kwargs.get('confidence',0.5))
        except spotlight.SpotlightException as e:
            print("WARNING: Spot exception", str(e),file=sys.stderr)
            continue
        except HTTPError as e:
            print("ERROR: HTTP exception", str(e),file=sys.stderr)
            if kwargs.get('ignore'):
                continue
            else:
                sys.exit(2)
        for rawentity in entities:
            if kwargs.get('debug'):
                print(rawentity,file=sys.stderr)
            try:
                wordspan = sentence.resolveoffsets(rawentity['offset'], rawentity['offset'] + len(rawentity['surfaceForm']))
            except folia.InconsistentText as e:
                print("WARNING: ", str(e),file=sys.stderr)
            if not wordspan:
                print("WARNING: Unable to resolve entity", rawentity['surfaceForm'],file=sys.stderr)
            else:
                mode = kwargs.get('mode',1)
                if mode == 1:
                    cls = rawentity['URI']
                    entityset = ENTITYSET_MODE_1
                elif mode == 2:
                    cls = getclass(rawentity['types'].split(','))
                    if cls is None:
                        print("WARNING: Resolved entity does not specify any known types, skipping: ", rawentity['surfaceForm'],file=sys.stderr)
                        continue
                    entityset = ENTITYSET_MODE_2
                else:
                    raise ValueError("Invalid mode")
                entity = wordspan[0].add(folia.Entity, *wordspan, cls=cls, set=entityset)
                if kwargs.get('metrics'):
                    for key, value in rawentity:
                        if key not in ('URI', 'offset', 'surfaceForm'):
                            entity.append(folia.Metric, set=METRIC_SET, cls=key, value=str(value))
                if mode == 2:
                    entity.append(folia.Relation, cls="dbpedia", href=rawentity['URI'], set=RELATIONSET, format="application/rdf+xml")
    if kwargs.get('output', None) == '-':
        print(doc.xmlstring())
    else:
        doc.save(kwargs.get('output',None))


def main():
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s','--server', type=str,help="The URL to the spotlight webservice", action='store',default="http://api.dbpedia-spotlight.org/en",required=False)
    parser.add_argument('-m','--mode', type=int, help="Select a mode: 1) Directly assign individual classes, linking directly to the named entity 2) Assign broad named entity classes (person, location, etc..) and add a relation link to the specific entity resource", action='store',default=1)
    parser.add_argument('-c','--confidence', type=float, help="Confidence threshold", action='store',default=0.5)
    parser.add_argument('-l','--language', type=str, help="Apply only to elements classified as being in this language", action='store')
    parser.add_argument('-M','--metrics', help="Add metrics (similarity score, support)", action='store_true')
    parser.add_argument('-o','--output', help="Output to the specified file (only makes sense for one input file), use '-' for stdout", action='store')
    parser.add_argument('-i','--ignore', help="Ignore HTTP errors", action='store_true')
    parser.add_argument('-d','--debug', help="Debug", action='store_true')
    parser.add_argument('files', nargs='+', help='Input files (FoLiA XML)')
    args = parser.parse_args()
    for file in args.files:
        process(file, **args.__dict__)

if __name__ == '__main__':
    main()
