# coding: utf-8

import gc
import os
import plyvel
import logging
import numpy as np


def mb(number):
    return 1024 * 1024 * number


class MicroIndex(object):
    DELIMITER = chr(200)

    def __init__(self, data_dir):
        logging.info("Opennig index.")

        self.idx_ldb = plyvel.DB(os.path.join(data_dir, "idx"), create_if_missing=False)
        self.doc_ldb = plyvel.DB(os.path.join(data_dir, "doc"), create_if_missing=False)
        self.wrd_ldb = plyvel.DB(os.path.join(data_dir, "wrd"), create_if_missing=False)
        self.pos_ldb = plyvel.DB(os.path.join(data_dir, "pos"), create_if_missing=False)

        self.w2id_dict = {}
        self.p2id_dict = {}

        for w, w_id in self.wrd_ldb:
            self.w2id_dict[w] = w_id
        for p, p_id in self.pos_ldb:
            self.p2id_dict[p] = int(p_id)

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
                # doc_id, p_id, i, freq

                w_id_str = str(w_id)
                plist_doc_k = w_id_str + MicroIndex.DELIMITER + "D"
                plist_pos_k = w_id_str + MicroIndex.DELIMITER + "P"
                plist_idx_k = w_id_str + MicroIndex.DELIMITER + "I"
                plist_frq_k = w_id_str + MicroIndex.DELIMITER + "F"

                old_sz = idx_ldb.get(w_id_str, -1)

                if old_sz != -1:
                    sz = int(old_sz) + len(p_list)
                    old_plist_doc = np.fromstring(idx_ldb.get(plist_doc_k), dtype=np.uint32)
                    old_plist_pos = np.fromstring(idx_ldb.get(plist_pos_k), dtype=np.uint8)
                    old_plist_idx = np.fromstring(idx_ldb.get(plist_idx_k), dtype=np.uint8)
                    old_plist_frq = np.fromstring(idx_ldb.get(plist_frq_k), dtype=np.uint32)
                    new_plist_doc = [v[0] for v in p_list]
                    new_plist_pos = [v[1] for v in p_list]
                    new_plist_idx = [v[2] for v in p_list]
                    new_plist_frq = [v[3] for v in p_list]
                    doc = np.concatenate((old_plist_doc, np.array(new_plist_doc, dtype=np.uint32))).tostring()
                    pos = np.concatenate((old_plist_pos, np.array(new_plist_pos, dtype=np.uint8))).tostring()
                    idx = np.concatenate((old_plist_idx, np.array(new_plist_idx, dtype=np.uint8))).tostring()
                    frq = np.concatenate((old_plist_frq, np.array(new_plist_frq, dtype=np.uint32))).tostring()
                else:
                    sz = len(p_list)
                    doc = np.array([v[0] for v in p_list], dtype=np.uint32).tostring()
                    pos = np.array([v[1] for v in p_list], dtype=np.uint8).tostring()
                    idx = np.array([v[2] for v in p_list], dtype=np.uint8).tostring()
                    frq = np.array([v[3] for v in p_list], dtype=np.uint32).tostring()

                wb.put(w_id_str, str(sz))
                wb.put(plist_doc_k, doc)
                wb.put(plist_pos_k, pos)
                wb.put(plist_idx_k, idx)
                wb.put(plist_frq_k, frq)

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
    def create(data_dir, i_file, doc_cache_size=256000, idx_cache_size=2000000):

        idx_dict = {}
        doc_dict = {}
        wrd_dict = {}
        pos_dict = {}

        idx_ldb = plyvel.DB(os.path.join(data_dir, "idx"),
                            write_buffer_size=mb(256),
                            block_size=mb(1024),
                            bloom_filter_bits=8,
                            create_if_missing=True,
                            error_if_exists=True)
        doc_ldb = plyvel.DB(os.path.join(data_dir, "doc"),
                            write_buffer_size=mb(256),
                            block_size=mb(1024),
                            bloom_filter_bits=8,
                            create_if_missing=True,
                            error_if_exists=True)
        wrd_ldb = plyvel.DB(os.path.join(data_dir, "wrd"),
                            write_buffer_size=mb(256),
                            block_size=mb(1024),
                            bloom_filter_bits=8,
                            create_if_missing=True,
                            error_if_exists=True)
        pos_ldb = plyvel.DB(os.path.join(data_dir, "pos"),
                            write_buffer_size=mb(256),
                            block_size=mb(1024),
                            bloom_filter_bits=8,
                            create_if_missing=True,
                            error_if_exists=True)

        idx_size = 0
        total_bytes = 0
        MB = float(1024 * 1024)

        for doc_id, line in enumerate(i_file):
            total_bytes += len(line)

            tokens = MicroIndex.parse_line(line)

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
                    p_list.append((doc_id, p_id, i, freq))
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
        gc.collect()

        wrd_ldb.close()
        pos_ldb.close()
        idx_ldb.close()
        doc_ldb.close()
        gc.collect()

    def find(self, query, limit=256, offset=0, min_freq=0):

        posting_lists = [self.execute_subquery(sub_query, min_freq) for sub_query in query]
        intersected_lists = sorted(set.intersection(*posting_lists))

        documents = []

        if offset < 0:
            offset = 0
        elif offset > len(intersected_lists):
            offset = intersected_lists

        if limit < 0:
            intersected_lists = intersected_lists[offset:]
        elif limit + offset > len(intersected_lists):
            intersected_lists = intersected_lists[offset:]
        else:
            intersected_lists = intersected_lists[offset:(limit + offset)]

        for doc_id in intersected_lists:
            doc = self.doc_ldb.get(str(doc_id)).split(self.DELIMITER)
            documents.append(doc)

        return documents

    def execute_subquery(self, sub_query, min_freq):
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

        if min_freq is not None and min_freq > 0:
            frqs_id = np.fromstring(self.idx_ldb.get(word_id + MicroIndex.DELIMITER + "F"), dtype=np.uint32)
            for i, doc_frq in enumerate(frqs_id):
                if doc_frq < min_freq:
                    doc_id = dics_id[i]
                    try:
                        dics_id_set.remove(doc_id)
                    except KeyError:
                        pass

        return dics_id_set

# if __name__ == "__main__":
#     assert(len(sys.argv) == 2)
#     logging.basicConfig(level=logging.INFO)

#     try:
#         MicroIndex.create(sys.argv[1], sys.stdin)
#     except Exception:
#         pass

#     mi = MicroIndex.open(sys.argv[1])

#     query_1 = ("putin", "vladimir")
#     query_2 = (("putin", "NN"), "vladimir")
#     query_3 = (("putin", "NN", None), "vladimir")
#     query_4 = (("putin", "NN", 1), ("vladimir", "NN", 2))

#     result = mi.find(query=(("vladimir_putin", "NN", 1),), limit=1, offset=0, min_freq=100)

#     for d in result:
#         print d
