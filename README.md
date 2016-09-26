# audiolabel

Python library for reading and writing label files for phonetic analysis (Praat, ELAN, ESPS, Wavesurfer, tabular data). This library is known to work well under Python 2.7 and was recently updated to work with Python 3, but Python 3 support has not been heavily tested. ELAN support is experimental.

# Overview

`audiolabel` reads phonetic labels files of various formats and parses them into three basic kinds of objects:

1. Labels
1. tiers in the form of PointTiers and IntervalTiers
1. LabelManagers

The usual way to read a file is to create a LabelManager with a filename and file type:

```
    from audiolabel import LabelManager
    lm = LabelManager(from_file='somefile.TextGrid', from_type='praat')
```

The LabelManager contains the label file's label tiers, and the tiers contain the individual annotations. We'll look at these object types in more detail.

# LabelManager

The LabelManager provides access to the individual tiers in a label file. The `.names` attribute stores the tier names:

```
    print(lm.names)
    # Output is ('word', 'phone', 'context')
```

You can use the tier() method to access the tiers by name or by the tier index, with the first tier assigned index 0:

```
    phontier = lm.tier(0)
    wordtier = lm.tier('word')
    contexttier = lm.tier(2)
```

Tier names are commonly found in Praat textgrids, but other label file types might not include names and require access to tiers by index.

# PointTiers and IntervalTiers

A label tier is an array of individual Labels, ordered chronologically. Label tiers can be one of two types. A PointTier contains only Labels that are associated with a single point in time, and an IntervalTier contains only Labels that describe an interval and are associated with two points in time.

A simple way to access the Labels in a tier is to iterate over its contents:

```
    for word in wordtier:
        print(word.t1, word.text)
```

Another way to access a Label in a tier is with the label_at() method, which returns a Label object corresponding to a time:

```
    word1 = wordtier.label_at(1.0)
    print(word1.text)
```

The tslice() method works much like the Array slice() method, but uses time-based indexing rather than integer indexes:

```
    for word in wordtier.tslice(0.4, 0.6):
        print(word.t1, word.text)
```

The search() method returns an Array of Label objects that match a regular expression pattern:

```
    # Iterate over all words containing 'r'
    for word in wordtier.search('r'):
        print(word.t1, word.text)
```

The Labels in a tier are ordered chronologically, and the `next()` and `prev()` methods provide access to Labels that follow or precede another Label.

```
    # Print the content of all Labels containing 'r' and the following Label
    for word in wordtier.search('r'):
        print(word.text, wordtier.next(word).text)
```

These methods also have a `skip` parameter that allows you to skip over one or more intervening labels:

```
    # Get the label that two labels that precede a label.
    prevword = wordtier.prev(word)             # By default skip=0
    preprevword = wordtier.prev(word, skip=1)  # The label before prevword
```

# Labels

Label objects hold individual annotations and are associated with a point in time or a time interval, and these are accessed by the Label attributes:

```
    print(word.t1)    # start of an interval Label, point in time of a point Label
    print(word.text)  # the Label content (annotation)
```

Labels that represent intervals rather than points in time have additional meaningful attributes:

```
   print(word.t1)       # end of an interval Label
   print(word.center)   # midpoint of the interval
   print(word.duration) # duration of the interval
```


