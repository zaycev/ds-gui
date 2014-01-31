Dependency store web service
===================

A dependency store, i.e. a collection of dependency relations with assigned frequencies. This web service provides an access to 5 dependency stores:

- English
- English generalized
- Russian
- Russian generalized
- Spanish

**Building Dependency Stores**

We build upon the idea that by parsing a sentence and abstracting from its syntactic structure (e.g.,
dropping modifiers) we can obtain common sense knowledge. For example, the sentence *Powerful summer storms left extensive damage in California* reveals common sense knowledge about storms possibly leaving damage and being powerful. This knowledge can be captured by tuples of words that have a determined pattern of syntactic relations among them. While many of such tuples can be erroneous due to parse errors, statistically higher frequency tuples can be considered more reliable.

We generated dependency tuples from parsed [English Gigaword](http://catalog.ldc.upenn.edu/LDC2003T05), [Spanish Gigaword](http://catalog.ldc.upenn.edu/LDC2011T12), [Russian ruwac](http://corpus.leeds.ac.uk/mocky/). The corpora were parsed using the following semantic processing pipelines:

- [English](https://github.com/metaphor-adp/Metaphor-ADP/tree/master/pipelines/English)
- [Spanish](https://github.com/metaphor-adp/Metaphor-ADP/tree/master/pipelines/Spanish)
- [Russian](https://github.com/metaphor-adp/Metaphor-ADP/tree/master/pipelines/Russian)

As one of the possible formats, the semantic processing pipelines output logical
forms of sentences in the style of [(Hobbs, 1985)](http://www.isi.edu/~hobbs/op-acl85.pdf), generalize over some syntactic constructions (e.g., passive/active), and performs binding of arguments. For example, the sentence *John decided to go to school* is represented as follows:

```
john-nn(e1,x1) & decide-vb(e2,x1,e3,u1) & go-vb(e3,x1,u2,u3) & to-in(e4,e3,x2) & school-nn(e5,x2)
```

The following dependency tuples can be extracted
from this output:

```
(subj-verb john decide)
(subj-verb john go)
(verb-verb decide go)
```

A dependency store is a collection of such tuples such that each tuple is assigned its frequency in a corpus. 

**Generalizing over Dependency Tuples**

A significant amount of the dependency tuples can be further generalized if we abstract from named
entities, synonyms, and sister terms. Consider the following NVNPN tuples:

```
(Guardian publish interview with Stevens)
(newspaper publish interview with John)
(journal publish interview with Dr. Crick)
```

The first two tuples above provide evidence for generating the tuple *newspaper publish interview with person)*. All three tuples above can be generalized into *(periodical publish interview with person)*. Such generalizations help to refine frequencies assigned to tuples containing abstract nouns and infer new tuples.

In order to obtain the generalizations, we first map nouns contained in the tuples into WordNet
and Wikipedia semantic nodes using the [YAGO](http://www.mpi-inf.mpg.de/yago-naga/yago/) ontology. Then we merge together tuples can contain arguments mapped to the same semantic nodes in YAGO.

---

The tools for building dependency stores can be found in [this repository](https://github.com/zaycev/mokujin).

---

**Contact**

- Vladimir Zaytsev ()
- Katya Ovchinnikova (e.ovchinnikova-AT-gmail.com)

