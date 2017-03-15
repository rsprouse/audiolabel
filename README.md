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

You can use the `tier()` method to access the tiers by name or by the tier index, with the first tier assigned index 0:

```
phontier = lm.tier(0)
wordtier = lm.tier('word')
contexttier = lm.tier(2)
```

Tier names are commonly found in Praat textgrids, but other label file types might not include names and require access to tiers by index.

The `labels_at()` method returns a tuple of Label objects from each of the tiers. If the label file provides tier names, then a namedtuple is returned, and as with `tier()` you can access the result by tier index or name:

```
labels = lm.labels_at(1.0)   # Get Label from all tiers at time 1.0
print(labels[0].text)        # Content of Label from phontier
print(labels.word.text)      # Content of Label from wordtier
print(labels[2].text)        # Content of Label from contexttier
```

Notice that the tier name is an attribute of the namedtuple and not a string.

The `scale_by()` method will multiply the time values of all Labels (in all tiers) by a scale factor:

```
lm.scale_by(1000)   # E.g. convert seconds to milliseconds
lm.scale_by(0.001)  # and back to seconds
```

And `shift_by()` shifts the time values of all Labels by an offset:

```
lm.shift_by(0.5)   # shift 0.5 seconds
lm.shift_by(-0.5)  # shift back
```

# PointTiers and IntervalTiers

A label tier is an array of individual Labels, ordered chronologically. Label tiers can be one of two types. A PointTier contains only Labels that are associated with a single point in time, and an IntervalTier contains only Labels that describe an interval and are associated with two points in time.

A simple way to access the Labels in a tier is to iterate over its contents:

```
for word in wordtier:
    print(word.t1, word.text)
```

Another way to access a Label in a tier is with the `label_at()` method, which returns a Label object corresponding to a time:

```
word1 = wordtier.label_at(1.0)
print(word1.text)
```

The `tslice()` method works much like array slicing, but uses time-based indexing rather than integer indexes:

```
for word in wordtier.tslice(0.4, 0.6):
    print(word.t1, word.text)
```

For more on `tslice()` see the 'Slicing and indexing' section.

The `search()` method returns a list of Label objects that match a regular expression pattern. The pattern can be provided as a string or as a precompiled regular expression.

```
# Iterate over all words containing 'r'.
for word in wordtier.search('r'):
    print(word.t1, word.text)
       
# Precompiled regex works too.
myre = re.compile('r')
for word in wordtier.search(myre):
    print(word.t1, word.text)
```

If the `return_match` parameter is set to `True` then `search()` returns a list of tuples containing the matching Labels and a regular expression match object. This feature is useful when your regular expression contains capture groups:

```
myre = re.compile('(?P<vowel>AH|EH|IH)(?P<stress>\d)')
for phone, match in phontier.search(myre, return_match=True):
    print(phone.text, match.group('vowel'), match.group('stress'))
```

The Labels in a tier are ordered chronologically, and the `next()` and `prev()` methods provide access to Labels that follow or precede another Label.

```
# Print the content of all Labels containing 'r' and the following Label content
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
print(word.t2)       # end of an interval Label
print(word.center)   # midpoint of the interval
print(word.duration) # duration of the interval
```

# Slicing and indexing

A label tier is a Python list and individual Label objects can be accessed with the usual integer indexing:

```
firstw = wordtier[0]  # first label in wordtier
threew = wordtier[:3] # list (slice) of first three labels
lastw = wordtier[-1]  # last label
```

Integer indexing is most useful for accessing the first and last labels in a tier. For non-initial, non-final Labels it is usually more convenient to use the time-based methods `label_at()` and `tslice()`.

The `label_at()` and `tslice()` methods provide an analog to integer indexing based on timestamps. However, the semantics of `tslice()` are a little different than integer indexing. Integer indexes always identify specific list elements, and time-based slicing can be ambiguous, especially for IntervalTiers. Consider this IntervalTier and a slice between 0.8 and 4.2 seconds (s1 and s2):

```
tier = audiolabel.IntervalTier()
for t1 in (range(5)):
    tier.add(audiolabel.Label(t1=float(t1), t2=float(t1+1), text='label'+str(t1)))

# Representation of tier
#    |          |          |          |         |          |
#    |  label0  |  label1  |  label2  |  label3 |  label4  |
#    |          |          |          |         |          |
#   0.0        1.0        2.0        3.0       4.0        5.0
#            ^                                     ^
#            |               <slice>               |
#            s1                                    s2
```

In this slice 'label0' and 'label4' partially overlap the specified interval. By default `tslice()` returns these partial overlaps, and you can exclude them by setting the `lstrip` ('left strip') and `rstrip` ('right strip') parameters to True:

```
tier.tslice(0.8, 4.2)                           # returns 'label0' through 'label4'
tier.tslice(0.8, 4.2, lstrip=True, rstrip=True) # returns 'label1' through 'label3'
tier.tslice(0.8, 4.2, lstrip=True)              # returns 'label1' through 'label4'
tier.tslice(0.8, 4.2, rstrip=True)              # returns 'label0' through 'label3'
```

Now consider a slice between 1.0 and 4.0 seconds:

```
#    |          |          |          |         |          |
#    |  label0  |  label1  |  label2  |  label3 |  label4  |
#    |          |          |          |         |          |
#   0.0        1.0        2.0        3.0       4.0        5.0
#               ^                               ^
#               |            <slice>            |
#               s1                              s2
```

The timepoints of this slice correspond to the boundary shared between two Labels. By default `tslice()` returns all the Labels matched by the timepoints, 'label0' through 'label4'. You can exclude the labels that only match at the edges by setting the `lincl` ('left include') and `rincl` ('right include) parameters to False:

```
tier.tslice(1.0, 4.0)                           # returns 'label0' through 'label4'
tier.tslice(1.0, 4.0, lincl=False, rincl=False) # returns 'label1' through 'label3'
tier.tslice(1.0, 4.0, lincl=False)              # returns 'label1' through 'label4'
tier.tslice(1.0, 4.0, rincl=False)              # returns 'label0' through 'label3'
```

In addition to the boundary ambiguity, there can be difficulty in comparing floating point values for equivalence. It is common to find that Labels on different annotation tiers are slightly misaligned. Sometimes this misalignment is not obvious and might be the result of truncation or roundoff errors in the normal course of processing files. In such cases, the misalignments are usually not meaningful, and you can relax the comparison so that values that are close to each other are considered to be equal. By default the tolerance of the comparison requires exact matches in order for two time values to be equal. You can use the `tol` parameter to relax the tolerance at both edges, and the `ltol` and `rtol` are added to `tol` to further adjust the left and right edges of `tslice()`:

```
tier.tslice(1.0001, 3.9999)                          # returns 'label1' through 'label3'
tier.tslice(1.0001, 3.9999, tol=0.01)                # returns 'label0' through 'label4'
tier.tslice(1.0001, 3.9999, ltol=0.01)               # returns 'label0' through 'label3'
tier.tslice(1.0001, 3.9999, tol=0.01, rtol=-0.01)    # returns 'label0' through 'label3'
```
