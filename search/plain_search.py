import json
import argparse
import logging
import microidx
import traceback

from microidx import MicroIndex

logger = logging.getLogger(__name__)

# initialize MicroIndex with data directory (containing idx, doc, wrd, pos, rlt)
indexes = {
    "eng":     (MicroIndex("/home/katya/Projects/dependency_store/indexes/ds_indexes/eng.ldb"),        "English")
}


def find(query,index,mfreq,rtype,rpage):

    #logging.info("%r\t%r\t%r\t%r\t%r" % (query, index,  mfreq, rtype))

    page_size = 256

    if index is None or index not in indexes:
        result = {
            "error":            True,
            "error_code":       1,
            "error_msg":        "Index key '%r' not found." % index,
            "found_triples":    [],
            "total_triples":    0,
            "pages":            0,
            "page":             0,
            "index":            index,
            "mfreq":            mfreq,
            "rtype":            rtype,
            "query":            str(query)
        }
        logging.error("Index key '%r' not found." % index)
        return result

    mi_index = indexes[index][0]

    try:
        query = mi_index.parse_query(query)
    except microidx.MicroIndexQueryParsingError:
        error_msg = traceback.format_exc()
        result = {
            "error":            True,
            "error_code":       2,
            "error_msg":        "Error while parsing query: %r" % error_msg,
            "found_triples":    [],
            "total_triples":    0,
            "pages":            0,
            "page":             0,
            "index":            index,
            "mfreq":            mfreq,
            "rtype":            rtype,
            "query":            str(query)
        }
        logging.error("Error while parsing query: %r" % error_msg)
        return result

    try:
        page = int(rpage) - 1
        if page < 0:
            page = 0
        offset = page * page_size
        result_page, result_size, offset = mi_index.find(query,
                                                         limit=page_size,
                                                         offset=offset,
                                                         rel_type=rtype,
                                                         min_freq=mfreq,
        )

        result = {
            "error":            False,
            "error_code":       None,
            "error_msg":        None,
            "found_triples":    result_page,
            "total_triples":    result_size,
            "index":            index,
            "mfreq":            mfreq,
            "rtype":            rtype,
            "query":            str(query)
        }
    except microidx.MicroIndexQueryExecutionError:
        error_msg = traceback.format_exc()
        result = {
            "error":            True,
            "error_code":       3,
            "error_msg":        "Error while executing query: %r" % error_msg,
            "found_triples":    [],
            "total_triples":    0,
            "index":            index,
            "mfreq":            mfreq,
            "rtype":            rtype,
            "query":            query
        }
        logging.error("Error while executing query: %r" % error_msg)
        return result

    logging.info("Found %d results. Returned %d starting from %d." % (result_size, page_size, offset))
    return result

def main():
	parser = argparse.ArgumentParser(description="Propstore search.")
	parser.add_argument("-q", help="Query.", default="")
	parser.add_argument("-i", help="Index.", default=None)
	parser.add_argument("-f", help="Minimal frequency.", default=0)
	parser.add_argument("-r", help="Relation type.", default=None)
	parser.add_argument("-p", help="Result page.", default=1)
	
	pa = parser.parse_args()

	query = pa.q.encode("utf-8") if pa.q else ""
	index = pa.i if pa.i else None
	mfreq = int(pa.f) if pa.f else 0
	rtype = pa.r if pa.r else None  #subj_verb_prep_compl,subj_verb_dirobj
	rpage = pa.p if pa.p else 1

	result = find(query,index,mfreq,rtype,rpage)
	print result
	return result

if __name__ == "__main__":
	main()
