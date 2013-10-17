# -*- coding: utf-8 -*-
"""
Created on Fri May 10 13:29:26 2013

@author: Ronald L. Sprouse (ronald@berkeley.edu)
@version: 0.1.2
l """

import numpy as np
import collections
import copy
import re
import logging

# Some convenience functions to be used in the classes.

# Strip white space at edges, remove surrounding quotes, and unescape quotes.
def _cleanPraatString(s):
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
    
    def __init__(self, t1, t2=None, text='', appdata=None, metadata=None,
                 *args, **kwargs):
        super(Label, self).__init__()
        if t1 == None:
            raise LabelTimeValueError('Missing t1 argument in __init__().')
        self._t1 = float(t1)  # Cast from string to be friendly.
        if t2 == None:
             self._t2 = t2  # This can be empty for point labels.
        else:
             self._t2 = float(t2)
        self.text = text
        self.appdata = appdata     # Container for app-specific data not used
                                   # by this class.
        
    def __repr__(self):
        if self._t2 == None:
            t2str = ''
        else:
            t2str = "t2={t2:0.4f}, ".format(t2=self._t2)
        return "Label( t1={t1:0.4f}, {t2}text='{text}' )".format(t1=self._t1,t2=t2str,text=self.text)

    def _repr_html_(self):
	"""Output for ipython notebook."""
        if self._t2 == None:
            t2str = ''
        else:
            t2str = "<b>t2</b>={t2:0.4f}, ".format(t2=self._t2)
        return "<b>Label</b>( <b>t1</b>={t1:0.4f}, {t2}<b>text</b>='{text}' )".format(t1=self._t1,t2=t2str,text=self.text)

    def _scaleBy(self, factor):
        self._t1 *= factor
        if self._t2 != None: self._t2 *= factor
        
    def _shiftBy(self, t):
        self._t1 += t
        if self._t2 != None: self._t2 += t

    def t1(self):
        """Return the first (possibly only) timepoint of the Label."""
        return self._t1

    def t2(self):
        """Return the second timepoint of the Label."""
        return self._t2
        
    def duration(self):
        """Return the duration of the label, or np.nan if the label represents a point
in time."""
        dur = np.nan
        if self._t2 != None:
            dur = self._t2 - self._t1
        return dur

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
        self.start = start
        self.end = end
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
        idx = np.searchsorted(self._time, label.t1())
        self._list.insert(idx, label)
        if len(self._time) > idx and np.isnan(self._time[idx]):
            self._time[idx] = label.t1()
        else:
            self._time = np.hstack([self._time[:idx], label.t1(), self._time[idx:]])
            
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

    def prev(self, label):
        """Return the label preceding label."""
        idx = self._list.index(label)
        if idx == 0:
            label = None
        else:
            label = self._list[idx-1]
        return label
          
    def first(self):
        """Return the first Label object."""
        try:
            return self._list[0]
        except:
            return None

    def last(self):
        """Return the last Label object."""
        try:
            return self._list[-1]
        except:
            return None

    def labelAt(self, time, method='closest'):
        """Return the label occurring at a particular time."""
        label = None
        if method == 'closest':
            idx = abs(self._time - time).argmin()
            label = self._list[idx]
        return label
        
    def search(self, pattern, returnMatch=False, **kwargs):
        """Return the ordered list of Label objects that contain pattern. If
        the returnMatch is True, return an ordered list of tuples that
        contain the matching labels and corresponding match objects."""
        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)
        if len(kwargs) == 0:
            labels = self._list
        else:
            labels = self.tslice(**kwargs)
        if returnMatch:
            return [(l,m) \
                    for l in labels \
                    for m in [pattern.search(l.text)] \
                    if m]
        else:
            return [l \
                    for l in labels \
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
            sl = [l for l in self._list if (l.t1() >= left and l.t1() <= right) ]
        elif lincl:
            sl = [l for l in self._list if (l.t1() >= left and l.t1() < right) ]
        elif rincl:
            sl = [l for l in self._list if (l.t1() > left and l.t1() <= right) ]
        else:
            sl = [l for l in self._list if (l.t1() > left and l.t1() < right) ]
        if t2 == None:
            if len(sl) > 1:
                raise IndexError(
                    "Found {:d} Labels while looking for one".format(len(sl))
                )
            elif len(sl) == 1:
                sl = sl[0]
        return sl

    def scaleBy(self, factor):
        """Multiply all annotation times by a factor."""
        for item in self:
            item._scaleBy(factor)

    def shiftBy(self, t):
        """Add a constant to all annotation times."""
        for item in self:
            item._shiftBy(t)

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
            sl = [l for l in self._list if (l.t2() >= left and l.t1() <= right) ]
        elif lincl:
            sl = [l for l in self._list if (l.t2() >= left and l.t1() < right) ]
        elif rincl:
            sl = [l for l in self._list if (l.t2() > left and l.t1() <= right) ]
        else:
            sl = [l for l in self._list if (l.t2() > left and l.t1() < right) ]
        if t2 == None:
            if len(sl) > 1:
                raise IndexError(
                    "Found {:d} Labels while looking for one".format(len(sl))
                )
            elif len(sl) == 1:
                sl = sl[0]
        return sl

    def labelAt(self, time, method='closest'):
        """Return the label occurring at a particular time."""
        label = None
        if method == 'closest':
            # FIXME: this implementation is will fail for some cases
            indexes = np.where(time >= self._time)
            idx = indexes[0][-1]
            label = self._list[idx]
        return label

class LabelManager(collections.MutableSet):
    """Manage one or more Tier objects."""
    
    def __init__(self, appdata=None, fromFile=None, fromType=None,
                 *args, **kwargs):
        super(LabelManager, self).__init__()
        self._tiers = []
        # Container for app-specific data not managed by this class.
        self.appdata = appdata
        if fromFile != None:
            if fromType == 'praat':
                self.readPraat(fromFile)
            elif fromType == 'praat_long':
                self.readPraatLong(fromFile)
            elif fromType == 'praat_short':
                self.readPraatShort(fromFile)
            elif fromType == 'esps':
                self.readESPS(fromFile)
            elif fromType == 'wavesurfer':
                self.readWavesurfer(fromFile)
            elif fromType == 'table':
                self.readTable(fromFile, **kwargs)
            # TODO: readIFCFormant is deprecated. Remove.
            elif fromType == 'ifcformant':
                self.readIFCFormant(fromFile)
              
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

    def tier(self, id, castTo=None, shiftLabels='left'):
        """Return the tier identified by id, which can be an integer index
or the tier name."""
# shiftLabels determines how label text associates to times.
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
        if castTo == "PointTier" and not isinstance(tier, PointTier):
            pttier = PointTier(start=tier.start, end=tier.end, name=tier.name)
            for lab in tier:
                ptlab = copy.deepcopy(lab)
                if shiftLabels == 'left':
# FIXME: don't use private attribute
                    ptlab._t1 = ptlab.t2()
# FIXME: don't use private attribute
                ptlab._t2 = None
                pttier.add(ptlab)
            tier = pttier
        elif castTo == "IntervalTier" and not isinstance(tier, IntervalTier):
            inttier = IntervalTier(start=tier.start, end=tier.end, name=tier.name)
            for lab in tier:
                intlab = copy.deepcopy(lab)
                if shiftLabels == 'left':
# FIXME: don't use private attribute
                    intlab._t2 = intlab.t1()
                else:
                    pass
                inttier.add(intlab)
            tier = inttier
        return tier

    # Get the label occurring at time t from specified tier (default 0). The
    # tier may identified by its index or name.
#    def labelAt(self, t, tier=0, mode='closest', tol=None):
#        """Get Label object at time t from tier."""
#        return self.tier(tier).labelAt(t, mode=mode, tol=tol)

#    def labels(self, tier=0):
#        return self.tier(tier).labels()
#        return self._tiers[tier]

    def names(self):
        """Return a list of tier names."""
        names = []
        for tier in self._tiers:
            names.append(tier.name)
        return names

    def labelsAt(self, time, method='closest'):
        """Return a tuple of Label objects corresponding to the tiers at time."""
        labels = []
        for tier in self._tiers:
            labels.append(tier.labelAt(time, method))
        names = self.names()
        # Check to make sure every tier name is valid (not empty, not
        # containing whitespace, not a duplicate). If one or more names is not
        # valid, return a regular tuple instead of a namedtuple.
        if '' not in names and None not in names:
            seen = []
            for name in self.names():
                if re.compile('\s').search(name) or name in seen:
                    labels = tuple(labels)
                    break
                else:
                    seen.append(name)
            if not isinstance(labels, tuple):
                Ret = collections.namedtuple('Ret', ' '.join(names))
                labels = Ret(*labels)
        return labels
            
        
    def readPraat(self, filename):
        """Populate labels by reading in a Praat file. The short/long format will be
guessed."""
        with open(filename, 'rb') as f:
            # decode() is will remove the BOM, if present.
            firstline = f.readline().decode('utf-8-sig').strip()
            if not re.match('File type = "ooTextFile"', firstline):
                raise LabelManagerParseError("File does not appear to be a Praat format.")
            f.readline()   # skip a line
            f.readline()   # skip a line
            xmin = f.readline()  # should be xmin = line
            if re.match('xmin = \d', xmin):
                f.close()
                self.readPraatLong(filename)
            elif re.match('\d', xmin):
                f.close()
                self.readPraatShort(filename)
            else:
                raise LabelManagerParseError("File does not appear to be a Praat format.")
        
    def readPraatShort(self, filename):
        with open(filename, 'rb') as f:
            firstline = f.readline().decode('utf-8-sig').strip()
            if not re.match(r'File type = "ooTextFile"', firstline):
                raise LabelManagerReadError("Could not read Praat short text grid.")
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
                if line == '': break   # Reached EOF.
                line = line.strip()


                if line == '': continue # Empty line.
                # Start a new tier.
                if line == '"IntervalTier"' or line == '"TextTier"':
                    if tier != None: self.add(tier)
                    tname = re.sub('^"|"$', '', f.readline().strip())
                    tstart = f.readline()
                    tend = f.readline()
                    numintvl = int(f.readline().strip())
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
                    else:

                        t2 = None
                    lab = Label(
                                t1=line,
                                t2=t2,
                                text=_cleanPraatString(f.readline())
                               )
                    tier.add(lab)
            if tier != None: self.add(tier)

    # Read the metadata section at the top of a tier in a praat_long file
    # referenced by f. Create a label tier from the metadata and return it.
    def _readPraatLongTierMetadata(self,f):
        d = dict(cls=None, tname=None, tstart=None, tend=None, numintvl=None)
        m = re.compile("class = \"(.+)\"").search(f.readline())
        d['cls'] = m.group(1)
        m = re.compile("name = \"(.+)\"").search(f.readline())
        d['tname'] = m.group(1)
        m = re.compile("xmin = (\d+)").search(f.readline())
        d['tstart'] = m.group(1)
        m = re.compile("xmax = (\d+)").search(f.readline())
        d['tend'] = m.group(1)
        m = re.compile("(?:intervals|points): size = (\d+)").search(f.readline())
        d['numintvl'] = m.group(1)
        if d['cls'] == 'IntervalTier':
            tier = IntervalTier(start=d['tstart'], end=d['tend'], \
                                  name=d['tname'], numlabels=d['numintvl'])
        else:
            tier = PointTier(start=d['tstart'], end=d['tend'], \
                                  name=d['tname'], numlabels=d['numintvl'])
        return tier

    def readPraatLong(self, filename):
        with open(filename, 'rb') as f:
            firstline = f.readline().decode('utf-8-sig').strip()
            if not re.match(r'File type = "ooTextFile"', firstline):
                raise LabelManagerReadError("Could not read Praat long text grid.")

            # Regexes to match line containing t1, t2, label text, and label end.
            # TODO: use named captures
            t1_re = re.compile("(?:xmin|number) = ([^\s]+)")
            t2_re = re.compile("xmax = ([^\s]+)")
            text_re = re.compile("^\s*(?:text|mark) = (\".*)")
            end_label_re = re.compile("^\s*(?:item|intervals|points) \[\d+\]:")
            item_re = re.compile("^\s*item \[\d+\]:")
                
            # Discard header lines.
            # TODO: use header lines for error checking or processing hints? Current
            # implementation ignores their content.
            while True:
                line = f.readline()
                if item_re.search(line): break
                # FIXME: better error
                if line == '': raise Exception("Could not read file.")
            
            tier = self._readPraatLongTierMetadata(f)
            
            # Don't use 'for line in f' loop construct since we use multiple
            # readline() calls in the loop.
            grabbing_labels = True
            t1 = t2 = text = None
            while grabbing_labels:
                toss = f.readline()  # skip "intervals|points [n]:" line
                t1line = f.readline()
                #print t1line
                m = t1_re.search(t1line)
                t1 = float(m.group(1))
                if isinstance(tier, IntervalTier):
                    m = t2_re.search(f.readline())
                    t2 = float(m.group(1))
                else:
                    t2 = None
                m = text_re.search(f.readline())
                text = m.group(1)
                grabbing_text = True
                while grabbing_text:
                    loc = f.tell()
                    line = f.readline()
                    if not (end_label_re.search(line) or line == ''):
                        text += line
                    else:
                        grabbing_text = False
                        lab = Label(
                            t1=t1,
                            t2=t2,
                            text=_cleanPraatString(text)
                        )
                        tier.add(lab)
                        if item_re.search(line):  # Start new tier.
                            self.add(tier)
                            tier = self._readPraatLongTierMetadata(f)
                        elif line == '': # Reached EOF
                            self.add(tier)
                            grabbing_labels = False
                        else:      # Found a new label line (intervals|points).
                            #f.seek(-len(line),1)  # Rewind to intervals|points.
                            f.seek(loc)

    def readESPS(self, filename, sep=None):
        """Read an ESPS label file."""
        
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
        empty_line = re.compile('^\s*#?.*$')
        
        with open(filename, 'rb') as f:
            while True:        # Process the header.
                line = f.readline()
                if not line:
                    raise LabelManagerParseError("Did not find header separator '#'!")
                    return None
                m = separator.search(line)
                if m: sep = m.group(1)
                if end_head.search(line): break
            while True:        # Process the body.
                line = f.readline()
                if not line: break
                if empty_line.search(line): continue
                (t1,color,content) = line.strip().split(None,2)
                for idx, val in enumerate(content.split(sep)):
                    try:
                        tier = self.tier(idx)
                    except IndexError:
                        #logging.debug("Adding tier for {:d}.\n".format(idx))
                        tier = PointTier()
                        self.add(tier)
                    tier.add(Label(t1=t1, text=val, appdata=color))
                
 
    def readWavesurfer(self, filename):
        """Read a wavesurfer label file."""
        with open(filename, 'rb') as f:
            tier = IntervalTier()
            for line in f:
                (t1,t2,text) = line.strip().split(None,2)
                tier.add(Label(t1=t1, t2=t2, text=text))
            self.add(tier)                

    def readTable(self, filename, sep='\t', fieldsInHead=True,
                  t1Col='t1', t2Col='t2', fields=None, skipN=0):
        """Generic reader for tabular file data."""
        with open(filename, 'rb') as f:
            for skip in range(skipN):
                f.readline()
            if fieldsInHead:
                fields = f.readline().rstrip().split(sep)
            else:
                fields = [fld.strip() for fld in fields.split(',')]
            tiers = []
            t1idx = fields.index(t1Col)
            fields[t1idx] = 't1'
            t2idx = None
            if t2Col in fields:
                t2idx = fields.index(t2Col)
                fields[t2idx] = 't2'
                for fld in fields:
                    if field == 't1' or field == 't2': continue
                    tiers.append(IntervalTier(name=fld))
            else:
                for fld in fields:
                    if fld == 't1': continue
                    tiers.append(PointTier(name=fld))
            t1 = t2 = tstart = tend = None
            for line in f.readlines():
                vals = line.rstrip('\n').split(sep)
                t1 = vals.pop(t1idx)
                if tstart == None: tstart = t1
                if t2idx != None: t2 = vals.pop(t2idx)
                for tier, val in zip(tiers, vals):
                    tier.add(Label(t1=t1, t2=t2, text=val))
            if t2 == None:
                tend = t1
            else:
                tend = t2
            for tier in tiers:
                tier.start = tstart
                tier.end = tend
                self.add(tier)
            

# TODO: implement the ability to pass fields, separator, fpfmt as to match parameters used when calling ifcformant                           
            # TODO: readIFCFormant is deprecated. Remove.
    def readIFCFormant(self, filename, sep='\t'):
        with open(filename, 'rb') as f:
            t_rms = PointTier(name='rms')
            t_f1 = PointTier(name='f1')
            t_f2 = PointTier(name='f2')
            t_f3 = PointTier(name='f3')
            t_f4 = PointTier(name='f4')
            t_f0 = PointTier(name='f0')
            tiers = [t_rms, t_f1, t_f2, t_f3, t_f4, t_f0]
            t = tstart = tend = None
            for line in f.readlines():
                fields = line.strip().split(sep)
                t = fields.pop(0)
                if tstart == None: tstart = t
                for tier, fld in zip(tiers, fields):
                    tier.add(Label(t1=t, text=fld))
            tend = t
            for tier in tiers:
                tier.start = tstart
                tier.end = tend
                self.add(tier)
                
if __name__ == '__main__':
    # FIXME: Remove this when done developing.
#    samplefile='C:\\Users\\ronald\\Desktop\\49_00_14_38_tony_49.TextGrid'
#    lm = LabelManager()
#    lm.read(samplefile)
#    print lm.tier('word').search('^FEEL$')

#    samplefile='C:\\src\\42_00_06_24_lynn_42.TextGrid'
#    lm2 = LabelManager()
#    lm2.readPraatLong(samplefile)
#    print lm2.tier('word').search('^she$')

#    samplefile='C:\\src\\test.ifc'
#    lm3 = LabelManager()
#    lm3.readIFCFormant(samplefile)
#    print lm3.tier('f1').search('189$')
#    print lm3.labelsAt(115)

#    samplefile='C:\\src\\phonlab\\annopy\\data\\s1703a.words'
#    lm4 = LabelManager()
#    lm4.readESPS(samplefile)
#    print lm4.tier(0).search('SIL')
#    print lm4.labelsAt(1)

#    samplefile='C:\\src\\phonlab\\annopy\\data\\wavesurfer1.lab'
#    lm5 = LabelManager()
#    lm5.readWavesurfer(samplefile)
#
    a = 1
    lm = LabelManager(fromFile='test/this_is_a_label_file.short.TextGrid', fromType='praat')
    pass
