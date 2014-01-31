# coding: utf-8

# Copyright (C) University of Southern California (http://usc.edu)
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

"""
Minimalistic inverted index for quering dependency store.
"""

import gc
import os
import plyvel
import logging
import traceback
import numpy as np


def mb(number):
    return 1024 * 1024 * number


class MicroIndexError(Exception):
    pass


class MicroIndexQueryParsingError(MicroIndexError):
    pass


class MicroIndexQueryExecutionError(MicroIndexError):
    pass


class MicroIndex(object):
    DELIMITER = chr(200)

    def __init__(self, data_dir):
        logging.info("Opennig index.")

        self.idx_ldb = plyvel.DB(os.path.join(data_dir, "idx"), create_if_missing=False)
        self.doc_ldb = plyvel.DB(os.path.join(data_dir, "doc"), create_if_missing=False)
        self.wrd_ldb = plyvel.DB(os.path.join(data_dir, "wrd"), create_if_missing=False)
        self.pos_ldb = plyvel.DB(os.path.join(data_dir, "pos"), create_if_missing=False)
        self.rlt_ldb = plyvel.DB(os.path.join(data_dir, "rlt"), create_if_missing=False)

        self.w2id_dict = {}
        self.p2id_dict = {}
        self.r2id_dict = {}

        for w, w_id in self.wrd_ldb:
            self.w2id_dict[w] = w_id
        for p, p_id in self.pos_ldb:
            self.p2id_dict[p] = int(p_id)
        for r, r_id in self.rlt_ldb:
            self.r2id_dict[r] = int(r_id)

    @staticmethod
    def open(data_dir):
        return MicroIndex(data_dir)

    @staticmethod
    def parse_line(line):
        return line.rstrip("\n").split(", ")

    @staticmethod
    def write_docs(doc_dict, doc_ldb):
        with doc_ldb.write_batch() as wb:
            for doc_id, doc_str in doc_dict.iteritems():
                wb.put(str(doc_id), doc_str)

    @staticmethod
    def write_idxs(idx_dict, idx_ldb):
        with idx_ldb.write_batch() as wb:
            for w_id, p_list in idx_dict.iteritems():
                # doc_id, p_id, i, freq, rlt_id

                w_id_str = str(w_id)
                plist_doc_k = w_id_str + MicroIndex.DELIMITER + "D"
                plist_pos_k = w_id_str + MicroIndex.DELIMITER + "P"
                plist_idx_k = w_id_str + MicroIndex.DELIMITER + "I"
                plist_frq_k = w_id_str + MicroIndex.DELIMITER + "F"
                plist_rlt_k = w_id_str + MicroIndex.DELIMITER + "R"

                old_sz = idx_ldb.get(w_id_str, -1)

                if old_sz != -1:
                    sz = int(old_sz) + len(p_list)
                    old_plist_doc = np.fromstring(idx_ldb.get(plist_doc_k), dtype=np.uint32)
                    old_plist_pos = np.fromstring(idx_ldb.get(plist_pos_k), dtype=np.uint8)
                    old_plist_idx = np.fromstring(idx_ldb.get(plist_idx_k), dtype=np.uint8)
                    old_plist_frq = np.fromstring(idx_ldb.get(plist_frq_k), dtype=np.uint32)
                    old_plist_rlt = np.fromstring(idx_ldb.get(plist_rlt_k), dtype=np.uint8)

                    new_plist_doc = [v[0] for v in p_list]
                    new_plist_pos = [v[1] for v in p_list]
                    new_plist_idx = [v[2] for v in p_list]
                    new_plist_frq = [v[3] for v in p_list]
                    new_plist_rlt = [v[4] for v in p_list]

                    doc = np.concatenate((old_plist_doc, np.array(new_plist_doc, dtype=np.uint32))).tostring()
                    pos = np.concatenate((old_plist_pos, np.array(new_plist_pos, dtype=np.uint8))).tostring()
                    idx = np.concatenate((old_plist_idx, np.array(new_plist_idx, dtype=np.uint8))).tostring()
                    frq = np.concatenate((old_plist_frq, np.array(new_plist_frq, dtype=np.uint32))).tostring()
                    rlt = np.concatenate((old_plist_rlt, np.array(new_plist_rlt, dtype=np.uint8))).tostring()

                else:
                    sz = len(p_list)
                    doc = np.array([v[0] for v in p_list], dtype=np.uint32).tostring()
                    pos = np.array([v[1] for v in p_list], dtype=np.uint8).tostring()
                    idx = np.array([v[2] for v in p_list], dtype=np.uint8).tostring()
                    frq = np.array([v[3] for v in p_list], dtype=np.uint32).tostring()
                    rlt = np.array([v[4] for v in p_list], dtype=np.uint8).tostring()

                wb.put(w_id_str, str(sz))
                wb.put(plist_doc_k, doc)
                wb.put(plist_pos_k, pos)
                wb.put(plist_idx_k, idx)
                wb.put(plist_frq_k, frq)
                wb.put(plist_rlt_k, rlt)

    @staticmethod
    def write_poss(pos_dict, pos_ldb):
        with pos_ldb.write_batch() as wb:
            for p, p_id in pos_dict.iteritems():
                wb.put(p, str(p_id))

    @staticmethod
    def write_wrds(wrd_dict, wrd_ldb):
        with wrd_ldb.write_batch() as wb:
            for w, w_id in wrd_dict.iteritems():
                wb.put(w, str(w_id))

    @staticmethod
    def write_rlts(rlt_dict, rlt_ldb):
        with rlt_ldb.write_batch() as wb:
            for rlt, rlt_id in rlt_dict.iteritems():
                wb.put(rlt, str(rlt_id))

    @staticmethod
    def create(data_dir, i_file, doc_cache_size=256000, idx_cache_size=1000000):

        idx_dict = {}
        doc_dict = {}
        wrd_dict = {}
        pos_dict = {}
        rlt_dict = {}

        idx_ldb = plyvel.DB(os.path.join(data_dir, "idx"),
                            write_buffer_size=mb(1024),
                            block_size=mb(512),
                            bloom_filter_bits=8,
                            create_if_missing=True,
                            error_if_exists=True)
        doc_ldb = plyvel.DB(os.path.join(data_dir, "doc"),
                            write_buffer_size=mb(1024),
                            block_size=mb(512),
                            bloom_filter_bits=8,
                            create_if_missing=True,
                            error_if_exists=True)
        wrd_ldb = plyvel.DB(os.path.join(data_dir, "wrd"),
                            write_buffer_size=mb(1024),
                            block_size=mb(512),
                            bloom_filter_bits=8,
                            create_if_missing=True,
                            error_if_exists=True)
        pos_ldb = plyvel.DB(os.path.join(data_dir, "pos"),
                            write_buffer_size=mb(1024),
                            block_size=mb(512),
                            bloom_filter_bits=8,
                            create_if_missing=True,
                            error_if_exists=True)
        rlt_ldb = plyvel.DB(os.path.join(data_dir, "rlt"),
                            write_buffer_size=mb(1024),
                            block_size=mb(512),
                            bloom_filter_bits=8,
                            create_if_missing=True,
                            error_if_exists=True)

        idx_size = 0
        total_bytes = 0
        MB = float(1024 * 1024)

        for doc_id, line in enumerate(i_file):
            total_bytes += len(line)

            tokens = MicroIndex.parse_line(line)

            rlt = tokens[0]
            rlt_id = rlt_dict.get(rlt, -1)
            if rlt_id == -1:
                rlt_id = len(rlt_dict)
                rlt_dict[rlt] = rlt_id

            freq = int(tokens[-1])

            for i in xrange(1, len(tokens) - 1):
                t = tokens[i]

                if t == "<->" or t == "<NONE>":
                    ws_id = []
                    p_id = -1
                else:

                    word_pos = t.split("-")
                    if len(word_pos) < 2:
                        ws_id = []
                        p_id = -1
                    else:

                        if len(word_pos) > 2:
                            ws = "-".join(word_pos[:-1])
                            p = word_pos[-1]
                        else:
                            ws, p = word_pos

                        p_id = pos_dict.get(p, -1)
                        if p_id == -1:
                            p_id = len(pos_dict)
                            pos_dict[p] = p_id

                        ws_id = []
                        for w in ws.split("||"):
                            w_id = wrd_dict.get(w, -1)
                            if w_id == -1:
                                w_id = len(wrd_dict)
                                wrd_dict[w] = w_id
                            ws_id.append(w_id)

                for w_id in ws_id:
                    p_list = idx_dict.get(w_id, [])
                    if len(p_list) == 0:
                        idx_dict[w_id] = p_list
                    p_list.append((doc_id, p_id, i, freq, rlt_id))
                    idx_size += 1

            doc_dict[doc_id] = MicroIndex.DELIMITER.join(tokens)

            if doc_id % doc_cache_size == 0:
                MicroIndex.write_docs(doc_dict, doc_ldb)
                logging.info("Processed %d documents (%.4f)." % (doc_id, total_bytes / MB))
                doc_dict = {}
                gc.collect()

            if idx_size % idx_cache_size == 0:
                MicroIndex.write_idxs(idx_dict, idx_ldb)
                logging.info("Merged index (%.4f)." % (total_bytes / MB))
                idx_dict = {}
                gc.collect()

        MicroIndex.write_docs(doc_dict, doc_ldb)
        logging.info("Processed %d documents (%.4f)." % (doc_id, total_bytes / MB))
        MicroIndex.write_idxs(idx_dict, idx_ldb)
        logging.info("Merged index (%.4f)." % (total_bytes / MB))
        MicroIndex.write_poss(pos_dict, pos_ldb)
        logging.info("Saved %d pos tags." % len(pos_dict))
        MicroIndex.write_wrds(wrd_dict, wrd_ldb)
        logging.info("Saved %d words." % len(wrd_dict))
        MicroIndex.write_rlts(rlt_dict, rlt_ldb)
        logging.info("Saved %d rel types." % len(rlt_dict))
        gc.collect()

        wrd_ldb.close()
        pos_ldb.close()
        idx_ldb.close()
        doc_ldb.close()
        gc.collect()

    def find(self, query, limit=256, offset=0, freq=(0, np.inf), rel_type=None):
        try:
            if rel_type == "*":
                rel_type = None
            posting_lists = [self.execute_subquery(sub_query, freq, rel_type) for sub_query in query]
            intersected_lists = sorted(set.intersection(*posting_lists))
            total_size = len(intersected_lists)
            documents = []
            if offset < 0:
                offset = 0
            elif offset > len(intersected_lists):
                offset = len(intersected_lists)
            if limit < 0:
                intersected_lists = intersected_lists[offset:]
            elif limit + offset > len(intersected_lists):
                intersected_lists = intersected_lists[offset:]
            else:
                intersected_lists = intersected_lists[offset:(limit + offset)]
            for doc_id in intersected_lists:
                doc = self.doc_ldb.get(str(doc_id)).split(self.DELIMITER)
                documents.append(doc)
            return documents, total_size, offset
        except Exception:
            raise MicroIndexQueryExecutionError("Error while executing query: %r." % query)

    def execute_subquery(self, sub_query, freq,  rel_type):
        print freq
        word, pos, idx = None, None, None
        if len(sub_query) == 0:
            raise ValueError("Zero size sub query.")
        if isinstance(sub_query, basestring):
            word = sub_query
        elif len(sub_query) == 1:
            word = sub_query,
        elif len(sub_query) == 2:
            word, pos = sub_query
        elif len(sub_query) == 3:
            word, pos, idx = sub_query
        else:
            raise ValueError("Large size (%d) sub query. Probably bad parse." % len(sub_query))
        word_id = self.w2id_dict.get(word, -1)
        if word_id == -1:
            return set()

        dics_id = np.fromstring(self.idx_ldb.get(word_id + MicroIndex.DELIMITER + "D"), dtype=np.uint32)
        dics_id_set = set(dics_id)

        if pos is not None and pos in self.p2id_dict:
            pos_id = self.p2id_dict[pos]
            poss_id = np.fromstring(self.idx_ldb.get(word_id + MicroIndex.DELIMITER + "P"), dtype=np.uint8)
            for i, doc_pos in enumerate(poss_id):
                if doc_pos != pos_id:
                    doc_id = dics_id[i]
                    dics_id_set.remove(doc_id)

        if idx is not None:
            idxs_id = np.fromstring(self.idx_ldb.get(word_id + MicroIndex.DELIMITER + "I"), dtype=np.uint8)
            for i, doc_idx in enumerate(idxs_id):
                if doc_idx != idx:
                    doc_id = dics_id[i]
                    try:
                        dics_id_set.remove(doc_id)
                    except KeyError:
                        pass

        min_freq, max_freq = freq
        if not (min_freq == 0 and max_freq == np.inf):
            frqs_id = np.fromstring(self.idx_ldb.get(word_id + MicroIndex.DELIMITER + "F"), dtype=np.uint32)
            for i, doc_frq in enumerate(frqs_id):
                if not (min_freq <= doc_frq <= max_freq):
                    doc_id = dics_id[i]
                    try:
                        dics_id_set.remove(doc_id)
                    except KeyError:
                        pass

        if rel_type is not None and rel_type in self.r2id_dict:
            rlt_id = self.r2id_dict[rel_type]
            rlts_id = np.fromstring(self.idx_ldb.get(word_id + MicroIndex.DELIMITER + "R"), dtype=np.uint8)
            for i, doc_rlt in enumerate(rlts_id):
                if doc_rlt != rlt_id:
                    doc_id = dics_id[i]
                    try:
                        dics_id_set.remove(doc_id)
                    except KeyError:
                        pass
        return dics_id_set

    @staticmethod
    def parse_query(query_str):
        """
        Format TERM_1:[POS_1]:[INDEX_1] [AND TERM_2:[POS_2]:[INDEX_2]] ...

        For example:

            "government"
            "government:NN"
            "government:NN:1"
            "government:NN:2"
            "government:*:2"
            "government:*:*"
            "government AND us"
            "government AND us:NN:2"

        """
        sub_queries = [t.replace(" ", "").split(":") for t in query_str.split(" AND ")]
        query = []
        try:
            for sub_query in sub_queries:
                word, pos, idx = None, None, None
                if len(sub_query) == 0:
                    continue
                if len(sub_query) == 1:
                    word = sub_query[0]
                elif len(sub_query) == 2:
                    word, pos = sub_query
                elif len(sub_query) == 3:
                    word, pos, idx = sub_query
                if pos is not None and pos == "*":
                        pos = None
                if idx is not None:
                    if idx == "*":
                        idx = None
                    else:
                        idx = int(idx)
                query.append((word, pos, idx))
            return query
        except Exception:
            raise MicroIndexQueryParsingError("Query parsing error: %r" % query_str)

    @staticmethod
    def parse_frequency(freq_str):
        """
        Frequency = MIN:MAX
        Frequency = :MAX
        Frequency = MIN:
        Frequency = MIN
        """
        if ":" in freq_str:
            if freq_str[0] == ":":    # :MAX
                f_min = 0
                f_max = int(freq_str.split(":")[1])
            elif freq_str[-1] == ":": # MIN:
                f_min = int(freq_str.split(":")[0])
                f_max = np.inf
            else:
                f_min, f_max = freq_str.split(":")
                f_min = int(f_min)
                f_max = int(f_max)
        else:
            f_min = int(freq_str)
            f_max = np.inf
        return f_min, f_max

if __name__ == "__main__":
    import sys

    assert(len(sys.argv) == 2)
    logging.basicConfig(level=logging.INFO)

    try:
        MicroIndex.create(sys.argv[1], sys.stdin)
    except Exception:
        logging.info("Index exists.")
