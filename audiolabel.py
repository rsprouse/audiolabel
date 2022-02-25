# -*- coding: utf-8 -*-
"""
Created on Fri May 10 13:29:26 2013

@author: Ronald L. Sprouse (ronald@berkeley.edu)
@version: 0.5.1
"""

from __future__ import division

import os, sys
import numpy as np
import pandas as pd
import codecs
import collections
import copy
import re

def read_label(fname, ftype, codec=None, tiers=None, addcols=[], stop_on_error=True, ignore_index=True):
    '''Read one or more label files and extract specified tiers as a list of
dataframes, one dataframe per tier.

Each tier dataframe will contain a row for every label found in the specified
tier from each of the label files. Each row has a column indicating the
start time of the label interval ('t1') and the end time ('t2'). The label
text is in another column, named 'label' by default. If the tiers parameter
is used and running under Python 3, the label column will be named with the
tier name, if provided as a string and the string is a valid column name
(e.g. doesn't contain spaces). A fourth column ('fname') is added to the
tier dataframe that indicates which label file was the source of the label row.

The label files are required to be similar--same type, same codec, and with
identical tier names.


Required parameters:

fname = list of label file filenames; for a single file this parameter can be
  provided as a string

ftype = the label file type; must be one of 'praat', 'praat_short',
  'praat_long', 'esps', 'wavesurfer'

Optional parameters:

codec = codec used to read the label files (e.g. 'utf-8', 'ascii');
  If codec is None, then Praat textgrids will default to 'utf-8' unless a
  file-specific encoding is detected. [default None]

tiers = int, str, list-like; tier name(s) or tier index(es) to read into
  DataFrames. DataFrames are returned in the same order as the list. If
  this parameter is not used or None, then all tiers will be returned as
  DataFrames. Every input label file must be compatible with the tier list.

addcols = list of additional DataFrame columns names to process and include
  in output DataFrames. Possible column names and values provided are:
  'barename': the label file's barename, with no path info or extension
  'dirname': the user-provided path to the label file without the filename
  'ext': the label file's extension
  'fidx': the idx of the label file in fname
   [default []]

stop_on_error = boolean; when True an error in processing an input file will 
  immediately reraise the error and no dataframes are returned; when False
  the error message is sent to STDERR and file processing continues, if
  possible. [default True]

ignore_index = boolean; value is passed to pd.concat()'s ignore_index
  parameter when DataFrames from a label file are concatenated to the
  existing tier DataFrames. When True, each tier DataFrame will have
  an index with range (0:N). When False, the index resets to 0 at the
  first row for each label file. [default True]
'''
    # Coerce to list if fname is a string.
    try:
        assert isinstance(fname, basestring) # Python 2
        fname = [fname]
    except AssertionError:
        pass
    except NameError:
        try:
            assert isinstance(fname, str) # Python 3
            fname = [fname]
        except AssertionError:
            pass

    if tiers is not None:
        # Coerce to list if tiers is a string or int.
        if isinstance(tiers, int):
            tiers = [tiers]
        else:
            try:
                assert isinstance(tiers, basestring) # Python 2
                tiers = [tiers]
            except AssertionError:
                pass
            except NameError:
                try:
                    assert isinstance(tiers, str) # Python 3
                    tiers = [tiers]
                except AssertionError:
                    pass

    dflist = None
    for fidx, f in enumerate(fname):
        dirname, basename = os.path.split(f)
        barename, ext = os.path.splitext(basename)
        assigndict = {'fname': f}  # Container for extra columns to assign()
        poss_add = {  # Possible columns to add.
            'barename': barename, 'fname': f, 'dirname': dirname,
            'fidx': fidx, 'ext': ext
        }
        for k, v in poss_add.items():
            if k in addcols:
                assigndict.update({k: v})

        try:
            lm = LabelManager(from_file=f, from_type=ftype, codec=codec)
            tlist = lm.as_df(tiers=tiers, includes=[])
            if dflist is None:
                dflist = [[] for t in tlist] # list of lists
        except Exception as e:
            if stop_on_error is True:
                raise e
            else:
                sys.stderr.write(e.msg())
                continue
        for idx, tr in enumerate(tlist):
            tr = tr.assign(**assigndict)
            dflist[idx].append(tr)

    # Make a list of tier DataFrames.
    dfs = [pd.concat(lst, ignore_index=ignore_index) for lst in dflist]

    # Rename column containing label text content.
    # If the tier parameter was not used, do not attempt to determine
    # the tier names in case the input list of label files has an
    # inconsistent number of tiers or tier names.
    if tiers is None:
        for df in dfs:
            df.rename(columns={'text': 'label'}, inplace=True)
    else:
        for df, tier in zip(dfs, tiers):
            tname = 'label'
            try:
                assert tier.isidentifier()
                tname = tier
            except (AssertionError, AttributeError):
                pass
            df.rename(columns={'text': tname}, inplace=True)

    # Cast some columns to type Categorical.
    catset = set(('barename', 'fname', 'dirname', 'ext'))
    for df in dfs:
        for c in list(catset & set(df.columns)): # intersection with catset
            df[c] = df[c].astype('category')

    return dfs
 
# Some convenience functions to be used in the classes.

# Strip white space at edges, remove surrounding quotes, and unescape quotes.
def _clean_praat_string(s):
    return re.sub('""', '"', re.sub('^"|"$', '', s.strip()))

class LabelError(Exception):
    """Base class for errors in this module."""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class LabelTimeValueError(LabelError):
    """Exceptions raised for incorrect time values."""
    pass
            
class LabelManagerError(LabelError):
    """Exceptions raised for missing annotation manager objects."""
    pass

class LabelManagerReadError(LabelError):
    """Exceptions raised for missing annotation manager objects."""
    pass

class LabelManagerMissingValueError(LabelError):
    """Exceptions raised for missing annotation objects."""
    pass

class LabelManagerParseError(LabelError):
    """Exceptions raised for missing annotation objects."""
    pass

# TODO: make content unicode-capable
class Label(object):
    """An individual annotation."""
    
    def __init__(self, text='', t1=None, t2=None, appdata=None, metadata=None,
                 codec='utf-8', *args, **kwargs):
        super(Label, self).__init__()
        if t1 == None:
            raise LabelTimeValueError('Missing t1 argument in __init__().')
        try:
            self._t1 = float(t1)  # Cast from string to be friendly.
        except TypeError:         # t1 == None
            self._t1 = None
        try:
             self._t2 = float(t2)
        except TypeError:         # t2 == None
            self._t2 = None
        self.text = text
        self.codec = codec
        self.appdata = appdata     # Container for app-specific data not used
                                   # by this class.
        
    def __repr__(self):
        if self._t2 == None:
            t2str = ''
        else:
            t2str = "t2={t2:0.4f}, ".format(t2=self._t2)
        text = self.text
        try:
            text = self.text.encode(self.codec)
        except NameError:
            pass
        return "Label( t1={t1:0.4f}, {t2}text='{text}' )".format(
            t1=self._t1,
            t2=t2str,
            text=text
        )
        

    def _repr_html_(self):
        """Output for ipython notebook."""
        if self._t2 == None:
            t2str = ''
        else:
            t2str = "<b>t2</b>={t2:0.4f}, ".format(t2=self._t2)
        return "<b>Label</b>( <b>t1</b>={t1:0.4f}, {t2}<b>text</b>='{text}' )".format(t1=self._t1,t2=t2str,text=self.text)

    def _scale_by(self, factor):
        self._t1 *= factor
        if self._t2 != None: self._t2 *= factor
        
    def _shift_by(self, t):
        self._t1 += t
        if self._t2 != None: self._t2 += t

    @property
    def t1(self):
        """Return the first (possibly only) timepoint of the Label."""
        return self._t1

    @property
    def t2(self):
        """Return the second timepoint of the Label."""
        return self._t2
        
    @property
    def duration(self):
        """Return the duration of the label, or np.nan if the label represents a point
in time."""
        dur = np.nan
        if self._t2 != None:
            dur = self._t2 - self._t1
        return dur

    @property
    def center(self):
        """Return the time centerpoint of the label. If the label represents
a point in time, return the point."""
        ctr = self._t1
        if self._t2 != None:
            ctr = (self._t1 + self._t2) / 2.0
        return ctr


class _LabelTier(collections.MutableSet):
    """A manager of (point) Label objects"""
    
    def __init__(self, start=0.0, end=float('inf'), name='', numlabels=None):
        super(_LabelTier, self).__init__()
        self.name = name
        self.start = float(start)
        self.end = float(end)
        self.extra_data = {} # Container for additional file-specific data.
        self._list = []      # Container for Label objects.
        # Array of starting (t1) timepoints used for calculations.
        if numlabels == None:
            self._time = np.array([])
        else:    # Preallocate array.
            self._time = np.empty(int(numlabels))
            self._time[:] = np.nan

    def __repr__(self):
        s = "[" + ",".join(repr(l) for l in self._list) + "]"
        return s

    def _repr_html_(self):
        """Output for ipython notebook."""
        s = "<ul>[<li>"
        if len(self._list) > 10:
            s += "</li><li>".join(self._list[n]._repr_html_() for n in range(5))
            s += "</li><li>...</li><li>"
            s += "</li><li>".join(self._list[n]._repr_html_() for n in range(-5,0))
        else:
            s += "</li><li>".join(l._repr_html_() for l in self._list)
        s += "</li>]</ul>"
        return s


#### Methods required by abstract base class ####

    def __contains__(self, x):
        return self._list.__contains__(x)
    
    def __iter__(self):
        return iter(self._list)
    
    def add(self, label):
        """Add an annotation object."""
        idx = np.searchsorted(self._time, label.t1)
        self._list.insert(idx, label)
        if len(self._time) > idx and np.isnan(self._time[idx]):
            self._time[idx] = label.t1
        else:
            self._time = np.hstack([self._time[:idx], label.t1, self._time[idx:]])
            
    def discard(self, label):
        """Remove a Label object."""
        
        idx = self._list.index(label)
        self._list.remove(label)
        self._time = np.hstack([self._time[:idx], self._time[idx+1:]])
    
    def __len__(self):
       return len(self._list)
       
    def _from_iterable(self, iterable):
        """The default constructor does not allow construction from an iterable,
which causes mixins inherited from Set to fail. This method handles construction
from an iterable."""
# FIXME: not implemented. also need to implement in derived classes for casts from other derived classes. Or implement equivalent functionality in LabelManager?
        pass

#### End of methods required by abstract base class ####

    def __getitem__(self, key):
        '''Allow indexing of tier like a list.'''
        return self._list[key]

    def prev(self, label, skip=0):
        """Return the label preceding label. Use the skip parameter to return an earlier label, e.g. skip=1 returns the second preceding label."""
        idx = self._list.index(label) - skip - 1
        try:
            label = self._list[idx]
        except IndexError:
            label = None
        return label
          
    def next(self, label, skip=0):
        """Return the label following label. Use the skip parameter to return a later label, e.g. skip=1 returns the second label after label."""
        idx = self._list.index(label) + skip + 1
        try:
            label = self._list[idx]
        except IndexError:
            label = None
        return label
          
    def label_at(self, time, method='closest'):
        """Return the label occurring at a particular time."""
        label = None
        if method == 'closest':
            idx = abs(self._time - time).argmin()
            label = self._list[idx]
        return label
        
    def search(self, pattern, return_match=False, **kwargs):
        """Return the ordered list of Label objects that contain pattern. If
        the return_match is True, return an ordered list of tuples that
        contain the matching labels and corresponding match objects."""
        try:    # Python 2
            if isinstance(pattern, basestring):
                pattern = re.compile(pattern)
        except NameError:    # Python 3
            if isinstance(pattern, str):
                pattern = re.compile(pattern)
        if len(kwargs) == 0:
            labels = self._list
        else:
            labels = self.tslice(**kwargs)
        if return_match:
            return [(l,m) \
                    for l in labels \
                    # TODO: verify that *not* encoding is the correct thing to do
#                    for m in [pattern.search(l.text.encode(l.codec))] \
                    for m in [pattern.search(l.text)] \
                    if m]
        else:
            return [l \
                    for l in labels \
                    # TODO: verify that *not* encoding is the correct thing to do
#                    if pattern.search(l.text.encode(l.codec))]
                    if pattern.search(l.text)]
        

    def tslice(self, t1, t2=None, tol=0.0, ltol=0.0, rtol=0.0, lincl=True, \
               rincl=True):
        """Return a time slice, an ordered list of Labels in the given time
        range."""
        # tol: symmetrical tolerance for exact match (extended by ltol/rtol)
        # ltol/rtol: tolerances on left/right side of time range (in addition to tol).
        # lincl/rincl: whether to include exact match on left/right of time range.
        left = t1 - tol - ltol
        right = None
        sl = []
        if t2 == None:  # Looking for a single match.
            right = t1 + tol + rtol
        else:
            right = t2 + tol + rtol
        if lincl and rincl:
            sl = [l for l in self._list if (l.t1 >= left and l.t1 <= right) ]
        elif lincl:
            sl = [l for l in self._list if (l.t1 >= left and l.t1 < right) ]
        elif rincl:
            sl = [l for l in self._list if (l.t1 > left and l.t1 <= right) ]
        else:
            sl = [l for l in self._list if (l.t1 > left and l.t1 < right) ]
        if t2 == None:
            if len(sl) > 1:
                raise IndexError(
                    "Found {:d} Labels while looking for one".format(len(sl))
                )
            elif len(sl) == 1:
                sl = sl[0]
        return sl

    def scale_by(self, factor):
        """Multiply all annotation times by a factor."""
        for item in self:
            item._scale_by(factor)
        self._time *= factor

    def shift_by(self, t):
        """Add a constant to all annotation times."""
        for item in self:
            item._shift_by(t)
        self._time += t

    # TODO: come up with a good name and calling convention, then make 
    # this a normal (non-hidden) method; change in subclasses too.
    def _as_string(self, fmt=None):
        sys.stderr.write('''WARNING: _as_string() is deprecated and will be removed in a later version.
Please use as_string() instead.
'''
        )
        return self.as_string(fmt=fmt)

    def as_string(self, fmt=None):
        """Return the tier as a string of label file type fmt. To be implemented in a subclass."""
        pass

    def as_df(self, includes=['duration', 'center']):
        """Return the tier as a Pandas DataFrame. To be implemented in a subclass."""
        pass

class PointTier(_LabelTier):
    """A manager of (point) Label objects"""
    def __init__(self, start=0.0, end=float('inf'), name='', numlabels=None, *args, **kwargs):
        super(PointTier, self).__init__(start, end, name, numlabels, *args, **kwargs)

    def __repr__(self):
        s = "PointTier("
        s += super(PointTier, self).__repr__()
        return s + ")\n"

    def _repr_html_(self):
        """Output for ipython notebook."""
        s = "<p><b>PointTier</b>( "
        s += super(PointTier, self)._repr_html_()
        return s + " )</p>"

    def _as_string(self, fmt=None):
        sys.stderr.write('''WARNING: _as_string() is deprecated and will be removed in a later version.
Please use as_string() instead.
'''
        )
        return self.as_string(fmt=fmt)

    def as_string(self, fmt=None):
        """Return the tier as a string of type fmt."""
        if fmt == 'praat_long':
            labels = [
                '        class = "TextTier"',
                '        name = "{:s}"'.format(self.name),
                "        xmin = {:0.12f}".format(self.start),
                "        xmax = {:0.12f}".format(self.end),
                "        points: size = {:d}".format(len(self))
            ]
            for idx,lab in enumerate(self._list):
                lab = '\n'.join((
                    "        points [{:d}]:".format(idx+1),
                    "            number = {:1.20f}".format(lab.t1),
                    '            mark = "{:s}"'.format(
                                     lab.text.replace('"', '""')
                                 )
                ))
                labels.append(lab)
            return '\n'.join(labels)
        elif fmt == 'praat_short':
            labels = [
                '"TextTier"',
                '"{:s}"'.format(self.name),
                "{:0.12f}".format(self.start),
                "{:0.12f}".format(self.end),
                "{:d}".format(len(self))
            ]
            for lab in self._list:
                lab = '\n'.join((
                    "{:1.20f}".format(lab.t1),
                    '"{:s}"'.format(lab.text.replace('"', '""'))
                ))
                labels.append(lab)
            return '\n'.join(labels)
        elif fmt == 'esps':
            # TODO: implement
            pass
        elif fmt == 'wavesurfer':
            pass
            # TODO: implement

    def as_df(self):
        """Return the tier as a Pandas DataFrame."""
        t1 = pd.Series(self._time)
        text = pd.Series([None] * len(t1))

        for idx, label in enumerate(self):
            text[idx] = label.text

        df = pd.concat([t1, text], axis=1)
        df.columns = ['t1', 'text']
        return df

    def add(self, label):
        """Add an annotation object."""
        super(PointTier, self).add(label)
        if self.end == np.Inf or label.t1 > self.end:
            self.end = label.t1
            
    # TODO: add discard() and adjust self.end?
    
class IntervalTier(_LabelTier):
    """A manager of interval Label objects"""
    def __init__(self, start=0.0, end=float('inf'), name='', numlabels=None, *args, **kwargs):
        super(IntervalTier, self).__init__(start, end, name, numlabels, *args, **kwargs)
    # Get/set start time of list of point annotations.

    def __repr__(self):
        s = "IntervalTier("
        s += super(IntervalTier, self).__repr__()
        return s + ")\n"

    def _repr_html_(self):
        """Output for ipython notebook."""
        s = "<p><b>IntervalTier</b>( "
        s += super(IntervalTier, self)._repr_html_()
        return s + " )</p>"

    def _as_string(self, fmt=None):
        sys.stderr.write('''WARNING: _as_string() is deprecated and will be removed in a later version.
Please use as_string() instead.
'''
        )
        return self.as_string(fmt=fmt)

    def as_string(self, fmt=None):
        """Return the tier as a string of type fmt."""
        if fmt == 'praat_long':
            labels = [
                '        class = "IntervalTier"',
                '        name = "{:s}"'.format(self.name),
                "        xmin = {:0.12f}".format(self.start),
                "        xmax = {:0.12f}".format(self.end),
                "        intervals: size = {:d}".format(len(self))
            ]
            for idx,lab in enumerate(self._list):
                lab = '\n'.join((
                    "        intervals [{:d}]:".format(idx+1),
                    "            xmin = {:1.20f}".format(lab.t1),
                    "            xmax = {:1.20f}".format(lab.t2),
                    '            text = "{:s}"'.format(
                                     lab.text.replace('"', '""')
                                 )
                ))
                labels.append(lab)
            return '\n'.join(labels)
        elif fmt == 'praat_short':
            labels = [
                '"IntervalTier"',
                '"{:s}"'.format(self.name),
                "{:0.12f}".format(self.start),
                "{:0.12f}".format(self.end),
                "{:d}".format(len(self))
            ]
            for lab in self._list:
                lab = '\n'.join((
                    "{:1.20f}".format(lab.t1),
                    "{:1.20f}".format(lab.t2),
                    '"{:s}"'.format(lab.text.replace('"', '""'))
                ))
                labels.append(lab)
            return '\n'.join(labels)
        elif fmt == 'esps':
            # TODO: implement
            pass
        elif fmt == 'wavesurfer':
            pass
            # TODO: implement

    def as_df(self, includes=['duration', 'center']):
        """Return the tier as a Pandas DataFrame.
The includes parameter is a list of strings that identify precalculated
columns to be included as a convenience. By default these columns are 
'duration' (t2 - t1) and 'center' ((t2 + t1) / 2). Since the information
in these columns can be calculated from t1 and t2 you can reduce the
memory usage of the DataFrame by excluding one or both of these strings
from the includes list."""
        t1 = pd.Series(self._time)
        t2 = pd.Series([np.nan] * len(t1))
        text = pd.Series([None] * len(t1))
        if 'duration' in includes:
            dur = pd.Series([None] * len(t1), dtype=np.float64)
        if 'center' in includes:
            ctr = pd.Series([None] * len(t1), dtype=np.float64)

        for idx, label in enumerate(self):
            t2[idx] = label.t2
            text[idx] = label.text
            if 'duration' in includes:
                dur[idx] = label.duration
            if 'center' in includes:
                ctr[idx] = label.center

        cols = ['t1', 't2', 'text']
        df = pd.concat([t1, t2, text], axis=1)
        if 'duration' in includes:
            cols.extend(['duration'])
            df = pd.concat([df, dur], axis=1)
        if 'center' in includes:
            cols.extend(['center'])
            df = pd.concat([df, ctr], axis=1)
        df.columns = cols
        return df

    def add(self, label):
        """Add an annotation object."""
        super(IntervalTier, self).add(label)
        if self.end == np.Inf or label.t2 > self.end:
            self.end = label.t2
            
    # TODO: add discard() and adjust self.end?
    
    def tslice(self, t1, t2=None, tol=0.0, ltol=0.0, rtol=0.0, lincl=True, \
               rincl=True, lstrip=False, rstrip=False):
        """Return a time slice, an ordered list of Labels in the given time
        range."""
        # tol: symmetrical tolerance for exact match (extended by ltol/rtol)
        # ltol/rtol: tolerances on left/right side of time range (in addition to tol).
        # lincl/rincl: whether to include exact match on left/right of time range.
        # lstrip/rstrip: (move to duration tier only) whether to remove duration
        #   labels that fall partially outside of the time range.
        left = t1 - tol - ltol
        right = None
        sl = []
        if t2 == None:  # Looking for a single match.
            right = t1 + tol + rtol
        else:
            right = t2 + tol + rtol
        if lincl and rincl:
            sl = [l for l in self._list if (l.t2 >= left and l.t1 <= right) ]
        elif lincl:
            sl = [l for l in self._list if (l.t2 >= left and l.t1 < right) ]
        elif rincl:
            sl = [l for l in self._list if (l.t2 > left and l.t1 <= right) ]
        else:
            sl = [l for l in self._list if (l.t2 > left and l.t1 < right) ]
        if lstrip is True and sl[0].t1 < left:
            sl = sl[1:]
        if rstrip is True and sl[-1].t2 > right:
            sl = sl[:-1]
        if t2 == None:
            if len(sl) > 1:
                raise IndexError(
                    "Found {:d} Labels while looking for one".format(len(sl))
                )
            elif len(sl) == 1:
                sl = sl[0]
        return sl

    def label_at(self, time, method='closest'):
        """Return the label occurring at a particular time."""
        label = None
        if method == 'closest':
            # FIXME: this implementation will fail for some cases
            indexes = np.where(time >= self._time)
            idx = indexes[0][-1]
            label = self._list[idx]
        return label

class LabelManager(collections.MutableSet):
    """Manage one or more Tier objects."""

    def __init__(self, from_file=None, from_type=None, 
                 codec=None, names=None, scale_by=None, shift_by=None,
                 appdata=None, *args, **kwargs):
        super(LabelManager, self).__init__()
        self._tiers = []
        self.codec = codec
        # Container for app-specific data not managed by this class.
        self.appdata = appdata
        if from_file != None:
            if from_type == 'praat':
                self.read_praat(from_file)
            elif from_type == 'praat_long':
                self.read_praat_long(from_file)
            elif from_type == 'praat_short':
                self.read_praat_short(from_file)
            elif from_type == 'eaf':
                self.read_eaf(from_file)
            elif from_type == 'esps':
                self.read_esps(from_file)
            elif from_type == 'wavesurfer':
                self.read_wavesurfer(from_file)
            elif from_type == 'table':
                self.read_table(from_file, **kwargs)
            if names is not None:
                self.names = names
            if scale_by is not None:
                self.scale_by(scale_by)
            # shift_by must be in the new time units after scale_by is applied
            if shift_by is not None:
                self.shift_by(shift_by)


    @property
    def names(self):
        """Return a tuple of tier names."""
        return tuple([tier.name for tier in self._tiers])

    @names.setter
    def names(self, names):
        """Set the name attributes in the LabelManager tiers, as specified
by the list in names. There can be fewer elements in names than the number
of tiers in the LabelManager. The strings in names are applied to the tiers
in order until names is exhausted. Remaining tiers in the LabelManager are
not renamed. To set a tier name to be empty use ''. The value None in
names indicates that the corresponding tier name should not be changed
from its current value."""
        for idx, name in enumerate(names):
            if names[idx] is not None:   # None indicates no change
                self.tier(idx).name = names[idx]

    def __repr__(self):
        s = "LabelManager(tiers="
        if len(self._tiers) > 0:
            s += "[" + ",".join(str(n) for n in range(len(self._tiers))) + "]"
            s += ", names=['" + "','".join([t.name for t in self._tiers]) + "']"
        else:
            s += "[]"
        return s + ")\n"
        
    def _repr_html_(self):
        """Output for ipython notebook."""
        s = "<p><b>LabelManager</b>( <b>tiers</b>="
        if len(self._tiers) > 0:
            s += "[" + ",".join(str(n) for n in range(len(self._tiers))) + "]"
            s += ", <b>names</b>=['" + "','".join([t.name for t in self._tiers]) + "']"
        else:
            s += "[]"
        return s + " )<p>"
        
    def _as_string(self, fmt=None):
        sys.stderr.write('''WARNING: _as_string() is deprecated and will be removed in a later version.
Please use as_string() instead.
'''
        )
        return self.as_string(fmt=fmt)

    def as_string(self, fmt=None):
        """Return the tiers as a string of type fmt."""
        if fmt == 'praat_long':
            tiers = [
                'File type = "ooTextFile"',
                'Object class = "TextGrid"',
                "",
                'xmin = {:0.20f}'.format(self._start()),
                'xmax = {:0.20f}'.format(self._end()),
                'tiers? <exists>',
                'size = {:d}'.format(len(self._tiers)),
                'item []:'
            ]
            for idx,tier in enumerate(self._tiers):
                tier = '\n'.join((
                    "    item [{:d}]:".format(idx+1),
                    tier.as_string('praat_long')
                ))
                tiers.append(tier)
            return '\n'.join(tiers)
        elif fmt == 'praat_short':
            tiers = [
                'File type = "ooTextFile"',
                'Object class = "TextGrid"',
                "",
                '{:0.20f}'.format(self._start()),
                '{:0.20f}'.format(self._end()),
                '<exists>',
                '{:d}'.format(len(self._tiers))
            ]
            for tier in self._tiers:
                tiers.append(tier.as_string('praat_short'))
            return '\n'.join(tiers)
        elif fmt == 'esps':
            # TODO: implement
            pass
        elif fmt == 'wavesurfer':
            pass
            # TODO: implement

    def as_df(self, tiers=None, includes=['duration', 'center']):
        """Return tiers as a list of Pandas DataFrames.
The tiers parameter is a list of tier identifiers that indicate the tiers
to be returned in the list of DataFrames. The identifiers may be tier names
or indexes. If the tiers parameter is None (default), then DataFrames for
all tiers are returned in the list.
The includes parameter is a list of precalculated columns that are included
in the DataFrames for convenience. By default these columns include 'duration'
and 'center', which are calculated from the Label t1 and t2. If you need to
reduce memory usage you can exclude one or both of these with
includes=['duration'], includes=['center'], or includes=[]."""
        if tiers is None:
            tiers = np.arange(len(self._tiers))
        dfs = []
        for tierid in tiers:
            tier = self.tier(tierid)
            if isinstance(tier, IntervalTier):
                df = self.tier(tierid).as_df(includes=includes)
            else:
                df = self.tier(tierid).as_df()
            dfs.append(df)
        return dfs

#### Methods required by abstract base class ####

    def __contains__(self, x):
        return self._tiers.__contains__(x)
    
    def __iter__(self):
        return iter(self._tiers)
    
    def add(self, tier, idx=None):
        """Add a Tier object."""
        if idx == None:
            self._tiers.append(tier)
        else:
            self._tiers.insert(idx, tier)
            
    def discard(self, tier):
        """Remove a tier object by passing in the tier object, its name, or its index."""
        if isinstance(tier, _LabelTier):
            t = tier
        else:
            t = self.tier(tier)
        self._tiers.remove(t)
    
    def __len__(self):
       return len(self._tiers)
       

#### End of methods required by abstract base class ####

    def tier(self, id, cast_to=None, shift_labels='left'):
        """Return the tier identified by id, which can be an integer index
or the tier name."""
# shift_labels determines how label text associates to times.
# Casting to PointTier:
#    left: associate point label text with interval label's t1
#    right: associate point label text with interval label's t2
# Casting to IntervalTier:
#    left: associate interval label text with preceding label and point label t1 and t2
#    right: associate interval label text using point label and following label as t1 and t2
        tier = None
        try:    # Try as an integer index first.
            tier = self._tiers[id]
        except TypeError:  # Must be a name.
            for t in self._tiers:
                if t.name == id:
                    tier = t
                    break
        if tier == None:
            raise IndexError("Could not find a tier with given id.")
        if cast_to == "PointTier" and not isinstance(tier, PointTier):
            pttier = PointTier(start=tier.start, end=tier.end, name=tier.name)
            for lab in tier:
                ptlab = copy.deepcopy(lab)
                if shift_labels == 'left':
# FIXME: don't use private attribute
                    ptlab._t1 = ptlab.t2
# FIXME: don't use private attribute
                ptlab._t2 = None
                pttier.add(ptlab)
            tier = pttier
        elif cast_to == "IntervalTier" and not isinstance(tier, IntervalTier):
            inttier = IntervalTier(start=tier.start, end=tier.end, name=tier.name)
            for lab in tier:
                intlab = copy.deepcopy(lab)
                if shift_labels == 'left':
# FIXME: don't use private attribute
                    intlab._t2 = intlab.t1
                else:
                    pass
                inttier.add(intlab)
            tier = inttier
        return tier

    def labels_at(self, time, method='closest'):
        """Return a tuple of Label objects corresponding to the tiers at time."""
        labels = tuple([tier.label_at(time,method) for tier in self._tiers])
#        for tier in self._tiers:
#            labels.append(tier.label_at(time, method))
        names = self.names
        # Check to make sure every tier name is valid (not empty, not
        # containing whitespace, not a duplicate). If one or more names is not
        # valid, return a regular tuple instead of a namedtuple.
        if '' not in names and None not in names:
            seen = []
            for name in self.names:
                if re.compile('\s').search(name) or name in seen:
                    labels = tuple(labels)
                    break
                else:
                    seen.append(name)
#            if not isinstance(labels, tuple):
            Ret = collections.namedtuple('Ret', ' '.join(names))
            labels = Ret(*labels)
        return labels
            
    def scale_by(self, factor):
        """Multiply all annotation times in all tiers by a factor."""
        for tier in self._tiers:
            tier.scale_by(factor)

    def shift_by(self, t):
        """Add a constant to all annotation times in all tiers."""
        for tier in self._tiers:
            tier.shift_by(t)

    def _get_open_args(self, filename):
        '''Get the right mode and encoding parameter values for open().

This method uses duck typing to determine whether we are running under
Python 3 (automatically decodes text files) or Python 2 (does not decode).
'''
        openargs = None
        try:
            with open(filename, encoding=self.codec) as f:
                openargs = {'mode': 'r', 'encoding': self.codec}
        except TypeError:
            openargs = {'mode': 'rb'}
        return openargs

    def detect_praat_encoding(self, filename):
        '''Guess and return the encoding of a file from the BOM. Limited to 'utf_8',
'utf_16_be', and 'utf_16_le'. Assume 'utf-8' if no BOM.'''
        has_bom = True
        # We want to read in binary mode under Python 2 or 3.
        with open(filename, 'rb') as f:
            firstline = f.readline()
            if firstline.startswith(codecs.BOM_UTF16_LE):
                detected_codec = 'utf_16_le'
            elif firstline.startswith(codecs.BOM_UTF16_BE):
                detected_codec = 'utf_16_be'
            elif firstline.startswith(codecs.BOM_UTF8):
                detected_codec = 'utf-8'
            else:
                detected_codec = 'utf-8'
                has_bom = False
        return (detected_codec, has_bom)

    def set_praat_encoding(self, filename):
        '''Set codec attribute for a Praat textgrid based on special logic. First
determine if the textgrid has a BOM. If BOM exists, use the codec that
it indicates. If it does not exist, use the codec suggested by the user. If user
does not suggest a codec, use utf-8 encoding as default.'''
        detected_codec, has_bom = self.detect_praat_encoding(filename)
        if has_bom is True:  # Trust BOM.
            if self.codec is not None and (self.codec != detected_codec):
               sys.stderr.write(
                   '''WARNING: overriding user-specified encoding {:}.
Found BOM for {:} encoding.\n'''.format(self.codec, detected_codec)
               )
            self.codec = detected_codec
        elif self.codec is None:  # Default
            self.codec = detected_codec

    def read_praat(self, filename):
        """Populate labels by reading in a Praat file. The short/long format will be
guessed."""
        self.set_praat_encoding(filename)
        openargs = self._get_open_args(filename)
        with open(filename, **openargs) as f:
            f.readline()   # skip a line
            f.readline()   # skip a line
            f.readline()   # skip a line
            xmin = f.readline()  # should be 'xmin = ' line
            if openargs['mode'] == 'rb':
                xmin = xmin.decode(self.codec)
            if re.match('xmin = \d', xmin):
                f.close()
                self.read_praat_long(filename)
            elif re.match('\d', xmin):
                f.close()
                self.read_praat_short(filename)
            else:
                raise LabelManagerParseError("File does not appear to be a Praat format.")
        
    def read_praat_short(self, filename):
        # Regex that indicates end of a label for lines that include opening
        # double quote.
        labendre = re.compile(
            '''
                (?:^"|[^"])
                (?:"")*      # Allow even number of preceding double quotes (Praat's way of including quotation marks in label content)
                "            # Line terminates with double quote
                \s*          # Ignore whitespace
                $
                |            # OR
                ^\s*"\s*$    # Only double quote and optional whitespace
            ''',
            re.VERBOSE
        )
        # Regex that indicates end of a label for lines that do not include
        # opening double quote, i.e. end of a multiline label text.
        mlabendre = re.compile(
            '''
                (?:^|[^"])
                (?:"")*      # Allow even number of preceding double quotes (Praat's way of including quotation marks in label content)
                "            # Line terminates with double quote
                \s*          # Ignore whitespace
                $
                |            # OR
                ^\s*"\s*$    # Only double quote and optional whitespace
            ''',
            re.VERBOSE
        )
        # Regex that matches a label line that is exactly quotation marks.
        onlyquotere = re.compile('^(?:"")+$')
        self.set_praat_encoding(filename)
        openargs = self._get_open_args(filename)
        with open(filename, **openargs) as f:
            firstline = f.readline()

            # Read in header lines.
            # TODO: use header lines for error checking or processing hints? Current
            # implementation ignores their content.
            tg = f.readline()
            blank = f.readline()
            start = f.readline()
            end = f.readline()
            exists = f.readline()
            numtiers = f.readline()

            # Don't use 'for line in f' loop construct since we use multiple
            # readline() calls in the loop.
            tier = None
            while True:
                line = f.readline()
                if openargs['mode'] == 'rb':
                    line = line.decode(self.codec)
                if line == '': break   # Reached EOF.
                line = line.strip()


                if line == '': continue # Empty line.
                # Start a new tier.
                if line == '"IntervalTier"' or line == '"TextTier"':
                    if tier != None: self.add(tier)
                    tname = re.sub('^"|"$', '', f.readline().strip())
                    tstart = f.readline()
                    tend = f.readline()
                    numintvl = f.readline()
                    if openargs['mode'] == 'rb':
                        tstart = tstart.decode(self.codec)
                        tend = tend.decode(self.codec)
                        numintvl = numintvl.decode(self.codec)
                    numintvl = int(numintvl.strip())
                    if line == '"IntervalTier"':
                        tier = IntervalTier(start=tstart, end=tend, \
                                                 name=tname, numlabels=numintvl)
                    else:
                        tier = PointTier(start=tstart, end=tend, \
                                              name=tname, numlabels=numintvl)
                # Add a label to existing tier.
                else:
                    if isinstance(tier, IntervalTier):
                        t2 = f.readline()
                        if openargs['mode'] == 'rb':
                            t2 = t2.decode(self.codec)
                    else:

                        t2 = None
                    labtext = f.readline()
                    if labendre.search(labtext.strip()) is None \
                        and onlyquotere.match(labtext.strip()) is None:
                        while True:
                            addline = f.readline()
                            labtext += addline
                            if mlabendre.search(addline) is not None:
                                break
                            elif addline == '':
                                msg = "Parse error. Unterminated label '" + labtext + "' in tier '" + tier.name + "'."
                                raise Exception(msg)
                    if openargs['mode'] == 'rb':
                        labtext = labtext.decode(self.codec)
                    lab = Label(
                                text=_clean_praat_string(labtext),
                                t1=line,
                                t2=t2,
                                codec=self.codec
                               )
                    tier.add(lab)
            if tier != None: self.add(tier)

    # Read the metadata section at the top of a tier in a praat_long file
    # referenced by f. Create a label tier from the metadata and return it.
    # Return None if metadata could not be read.
    def _read_praat_long_tier_metadata(self, f, mode=None):
        d = dict(cls=None, tname=None, tstart=None, tend=None, numintvl=None)
        try:
            line = f.readline()
            assert(line != '')
            if mode == 'rb':
                line = line.decode(self.codec)
            m = re.compile("class = \"(.+)\"").search(line)
            d['cls'] = m.group(1)
            line = f.readline()
            assert(line != '')
            if mode == 'rb':
                line = line.decode(self.codec)
            m = re.compile("name = \"(.+)\"").search(line)
            d['tname'] = m.group(1)
            line = f.readline()
            assert(line != '')
            if mode == 'rb':
                line = line.decode(self.codec)
            m = re.compile("xmin = (-?[\d.]+)").search(line)
            d['tstart'] = m.group(1)
            line = f.readline()
            assert(line != '')
            if mode == 'rb':
                line = line.decode(self.codec)
            m = re.compile("xmax = (-?[\d.]+)").search(line)
            d['tend'] = m.group(1)
            line = f.readline()
            assert(line != '')
            if mode == 'rb':
                line = line.decode(self.codec)
            m = re.compile("(?:intervals|points): size = (\d+)").search(line)
            d['numintvl'] = m.group(1)
        except AssertionError:
            pass
        if d['cls'] == 'IntervalTier':
            tier = IntervalTier(start=d['tstart'], end=d['tend'], \
                                  name=d['tname'], numlabels=d['numintvl'])
        elif d['cls'] in ['TextTier', 'PointTier']:
            tier = PointTier(start=d['tstart'], end=d['tend'], \
                                  name=d['tname'], numlabels=d['numintvl'])
        else:
            tier = None
        return tier

    def read_praat_long(self, filename):
        self.set_praat_encoding(filename)
        openargs = self._get_open_args(filename)
        with open(filename, **openargs) as f:
            firstline = f.readline()
            # Regexes to match line containing t1, t2, label text, and label end.
            # TODO: use named captures
            t1_re = re.compile("(?:xmin|number) = ([^\s]+)")
            t2_re = re.compile("xmax = ([^\s]+)")
            text_re = re.compile("^\s*(?:text|mark) = (\".*)")
            end_label_re = re.compile("^\s*(?:item|intervals|points)\s*\[\d+\]:?")
            item_re = re.compile("^\s*item\s*\[\d+\]:?")
                
            # Discard header lines.
            # TODO: use header lines for error checking or processing hints? Current
            # implementation ignores their content.
            while True:
                line = f.readline()
                if openargs['mode'] == 'rb':
                    line = line.decode(self.codec)
                if item_re.search(line): break
                # FIXME: better error
                if line == '': raise Exception("Could not read file.")
            
            tier = self._read_praat_long_tier_metadata(
                f, mode=openargs['mode']
            )
            
            # Don't use 'for line in f' loop construct since we use multiple
            # readline() calls in the loop.
            t1 = t2 = text = None
            while tier is not None:
                if len(tier._time) == 0:   # empty tier; go to next tier
                    self.add(tier)
                    f.readline() # skip "item [n]:' line 
                    tier = self._read_praat_long_tier_metadata(
                        f, mode=openargs['mode']
                    )
                    continue
                toss = f.readline()  # skip "intervals|points [n]:" line
                t1line = f.readline()
                if openargs['mode'] == 'rb':
                    t1line = t1line.decode(self.codec)
                m = t1_re.search(t1line)
                t1 = float(m.group(1))
                if isinstance(tier, IntervalTier):
                    t2line = f.readline()
                    if openargs['mode'] == 'rb':
                        t2line = t2line.decode(self.codec)
                    m = t2_re.search(t2line)
                    t2 = float(m.group(1))
                else:
                    t2 = None
                txtline = f.readline()
                if openargs['mode'] == 'rb':
                    txtline = txtline.decode(self.codec)
                m = text_re.search(txtline)
                text = m.group(1)
                grabbing_text = True
                while grabbing_text:
                    loc = f.tell()
                    line = f.readline()
                    if openargs['mode'] == 'rb':
                        line = line.decode(self.codec)
                    if not (end_label_re.search(line) or line == ''):
                        text += line
                    else:
                        grabbing_text = False
                        lab = Label(
                            text=_clean_praat_string(text),
                            t1=t1,
                            t2=t2,
                            codec=self.codec
                        )
                        tier.add(lab)
                        if item_re.search(line):  # Start new tier.
                            self.add(tier)
                            tier = self._read_praat_long_tier_metadata(
                                f, mode=openargs['mode']
                            )
                        elif line == '': # Reached EOF
                            self.add(tier)
                            tier = None
                        else:      # Found a new label line (intervals|points).
                            #f.seek(-len(line),1)  # Rewind to intervals|points.
                            f.seek(loc)

    def _start(self):
        """Get the start time of the tiers in the LabelManager."""
        return min([t.start for t in self._tiers])
        
    def _end(self):
        """Get the end time of the tiers in the LabelManager."""
        return max([t.end for t in self._tiers])
        
        
    def _get_praat_header(self, type=None):
        """Get the header (pre-tier) section of a Praat label file."""
        xmin = "{:1.16f}".format(self._start())
        xmax = "{:1.16f}".format(self._end())
        intervals = "{:d}".format(len(self._tiers))
        if type == 'long':
            xmin = "xmin = " + xmin
            xmax = "xmax = " + xmax
            intervals = "intervals: size = " + intervals
        return "\n".join((
            'File type = "ooTextFile"',
            'Object class = "TextGrid"',
            '',
            xmin,
            xmax,
            '<exists>',
            intervals
            ))

    # TODO: this works for karuk .eaf files; need to find out whether this is sufficient for all
    # .eaf files
    # TODO: This implementation does not retain all of the possible dependencies between tiers.
    #       This method should be rewritten to handle dependent tiers properly.
    def read_eaf(self, filename, codec='utf_8'):
        """Read an ELAN .eaf file."""
        # TODO: read encoding from xml document instead of hardcoding
        # utf_8?

        import xml.etree.ElementTree as ET
        tree = ET.parse(filename)
        root = tree.getroot()
        # Time subdivision tiers have sequences of annotations that
        # subdivide a parent tier's duration. The individual annotations
        # may have empty time slots. The first element in the sequence
        # shares the parent tier's first time slot, and the last element
        # of the sequence shares the parent's last time slot. All other
        # time slots are empty.
        tslots = {}
        tslot_tiers = {'t1': {}, 't2': {}}
        for slot in root.findall('.//TIME_ORDER/TIME_SLOT'):
            slot_id = slot.get('TIME_SLOT_ID')
            tslots[slot_id] = slot.get('TIME_VALUE')

        # Sort the tier names so that parent tiers are processed, and their
        # time slots filled out, before their children. That way we can
        # calculate time values for the empty time slots before they are
        # needed in the children.
        tmap = {tier.get('TIER_ID'): tier.get('PARENT_REF') for tier in root.findall('./TIER')}
        tiersort = []
        tkeys = list(tmap.keys())
        while len(tkeys) > 0:
            for name in tkeys:
                if tmap[name] is None or tmap[name] in tiersort:
                    tiersort.append(name)
                    tkeys.remove(name)

        # Preserve tier order.
        for idx,eaftier in enumerate(root.findall('./TIER')):
            tier = IntervalTier(name=eaftier.get('TIER_ID'))
            tier.extra_data['eaf'] = eaftier.attrib
            self.add(tier)

        # Process labels on parent tiers before dependent tiers so that
        # timeslots are filled in properly in the dependents.
        for name in tiersort:
            tier = self.tier(name)
            anno_run = []
            anno_run_length = None
            start_t = None
            end_t = None
            eaftier = root.find(".//TIER/[@TIER_ID='{}']".format(name))
            for anno in eaftier.findall('ANNOTATION/*'):
                anno_id = anno.get('ANNOTATION_ID')
                if anno.tag == 'ALIGNABLE_ANNOTATION':
                    t_anno = anno
                    anno_run_length = 1
                    start_t = float(tslots[t_anno.get('TIME_SLOT_REF1')])
                    end_t = float(tslots[t_anno.get('TIME_SLOT_REF2')])
                elif anno.tag == 'REF_ANNOTATION':
                    t_anno = None
                    ref = anno.get('ANNOTATION_REF')
                    if anno_run_length is None:
                        xpath = ".//TIER/[@TIER_ID='{}']/ANNOTATION/REF_ANNOTATION/[@ANNOTATION_REF='{}']".format(name,ref)
                        anno_run_length = len(root.findall(xpath))
                    start_t = float(tslot_tiers['t1'][ref])
                    end_t = float(tslot_tiers['t2'][ref])
                    # Tiers can be hierarchical. Loop through refs until we find the top.
                    while t_anno is None:
                        xpath = ".//ANNOTATION/REF_ANNOTATION/[@ANNOTATION_ID='{}']".format(ref)
                        try:
                            ref = root.find(xpath).get('ANNOTATION_REF')
                        except AttributeError:  # No more REF_ANNOTATION. At the top.
                            xpath = ".//ANNOTATION/ALIGNABLE_ANNOTATION/[@ANNOTATION_ID='{}']".format(ref)
                            t_anno = root.find(xpath)
                            if t_anno is None:
                                raise RuntimeError("Could not find annotation ref.")
                else:
                    raise RuntimeError("Unrecognized annotation type.")

                anno_run.append((anno_id, anno.find('ANNOTATION_VALUE').text))
                if len(anno_run) == anno_run_length:
                    step = (end_t - start_t) / anno_run_length
                    for idx,mypair in enumerate(anno_run):
                        the_id = mypair[0]
                        label = mypair[1]
                        if label is None:
                            label = ''
                        t1 = start_t
                        t2 = start_t + round((idx + 1) * step)
                        if idx > 0:
                            t1 += round(idx * step)
                        if idx == (anno_run_length - 1):
                            t2 = end_t
                        tier.add(Label(text=label, t1=t1, t2=t2, codec=codec))
                        tslot_tiers['t1'][the_id] = t1
                        tslot_tiers['t2'][the_id] = t2
                    anno_run = []
                    start_t = None
                    end_t = None
                    anno_run_length = None

    def read_esps(self, filename, sep=None):
        """Read an ESPS label file."""
        
        # The ESPS label file format encodes a single time for each label,
        # which appear to be similar to Praat PointTiers. In actual usage,
        # however, the ESPS tools encoded intervals, with the label text
        # associated with the end of the interval. We therefore read ESPS
        # files as IntervalTiers with the label's current time as t2, and
        # t1 is the preceding label's t2 (0.0 for the first label).

        # sep is the character used to separate 'tiers' (fields) in the
        # label content. The default is ';'. If the 'separator' field is
        # included in the file header, use that instead. If the sep parameter
        # is provided when calling this method, then it overrides the default
        # and file header values.

        # N.B. we do not use the 'nfields' field in the file header to
        # determine how many tiers to create. Experience shows that this
        # header field is not always well-maintained, so we simply create
        # tiers based on how many separators we find in the content.

        # Precompile regular expressions to identify the 'separator' header
        # line, end-of-header line, and empty/comment label lines.
        separator = re.compile('separator\s+(.+)')
        end_head = re.compile('^#')
        empty_line = re.compile('^\s*(#.*)?$')
        
        openargs = self._get_open_args(filename)
        with open(filename, **openargs) as f:
            # Process the header
            while True:
                line = f.readline()
                if not line:
                    raise LabelManagerParseError("Did not find header separator '#'!")
                    return None
                m = separator.search(line)
                if m: sep = m.group(1)
                if end_head.search(line): break

            # Process the body
            old_t2 = 0.0
            while True:
                line = f.readline()
                if not line: break
                if empty_line.search(line): continue
                try:
                  (t2,color,content) = line.strip().split(None,2)
                except ValueError:
                    try:
                        (t2,color) = line.strip().split(None,1)
                        content = ''
                    except ValueError:
                        t2 = line.strip()
                        color = ''
                        content = ''

                for idx, val in enumerate(content.split(sep)):
                    try:
                        tier = self.tier(idx)
                    except IndexError:
                        tier = IntervalTier()
                        self.add(tier)
                    tier.add(Label(text=val, t1=old_t2, t2=t2, appdata=color))
                    old_t2 = t2
                
 
    def read_wavesurfer(self, filename):
        """Read a wavesurfer label file."""
        openargs = self._get_open_args(filename)
        with open(filename, **openargs) as f:
            tier = IntervalTier()
            for line in f:
                (t1,t2,text) = line.strip().split(None,2)
                tier.add(Label(text=text, t1=t1, t2=t2))
            self.add(tier)                

    def read_table(self, infile, sep='\t', fields_in_head=True,
                  t1_col='t1', t2_col='t2', fields=None, skiplines=0,
                  t1_start=None, t1_step=None):
        """Generic reader for tabular file data. infile can be a filename or
open file handle. If t1_col is None, automatically create a t1 index with
first value t1_start and adding t1_step for subsequent values."""
        if t1_col is None and t1_start is None:
            t1_start = 0
        if t1_col is None and t1_step is None:
            t1_step = 1
        if self.codec is None:
            self.codec = 'utf-8'
        try:
            openargs = self._get_open_args(infile)
            f = open(infile, **openargs)
            binmode = openargs['mode'] == 'rb'
        except TypeError as e:  # infile should already be a file handle
            f = infile
            try:
                binmode = f.mode == 'rb'
            except AttributeError:
                # We get here if infile is a TextIOWrapper rather than a
                # file handle (as would be returned by 
                # subprocess.Popen(..., stdout=PIPE, universal_newlines=True)
                binmode = False

        for skip in range(skiplines):
            f.readline()

        # Process field names.
        if fields_in_head:
            fields = f.readline().rstrip().split(sep)
        else:
            try:
                if isinstance(fields, (str, unicode)):
                    fields = [fld.strip() for fld in fields.split(',')]
            except NameError:
                if isinstance(fields, (str)):
                    fields = [fld.strip() for fld in fields.split(',')]
        tiers = []
        if t1_col == None:
            t1idx = None
        else:
            t1idx = fields.index(t1_col)
            fields[t1idx] = 't1'
        t2idx = None
        if t2_col in fields:
            t2idx = fields.index(t2_col)
            fields[t2idx] = 't2'
            for fld in fields:
                if fld == 't1' or fld == 't2': continue
                tiers.append(IntervalTier(name=fld))
        else:
            for fld in fields:
                if fld == 't1': continue
                tiers.append(PointTier(name=fld))

        # Parse labels from rows.
        t1 = t2 = tstart = tend = None
        valsep = '\r\n'
        if binmode is True:
            sep = sep.encode(self.codec)
            valsep = valsep.encode(self.codec)
        for idx, line in enumerate([l for l in f.readlines() if l != '']):
            vals = [val.strip() for val in line.rstrip(valsep).split(sep)]
            if t1_start is not None and t1_step is not None:
                t1 = (idx * t1_step) + t1_start
                if t1idx is not None:
                    vals.pop(t1idx)
            else:
                t1 = vals.pop(t1idx)
                if binmode is True: t1 = t1.decode(self.codec)
            if tstart == None: tstart = t1
            if t2idx != None: t2 = vals.pop(t2idx)
            if binmode is True and t2 is not None: t2 = t2.decode(self.codec)
            for tier, val in zip(tiers, vals):
                if binmode is True: val = val.decode(self.codec)
                tier.add(Label(text=val, t1=t1, t2=t2))

        # Finish the tier.
        if t2 == None:
            tend = t1
        else:
            tend = t2
        for tier in tiers:
            tier.start = tstart
            tier.end = tend
            self.add(tier)

