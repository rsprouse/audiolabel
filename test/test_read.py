#!/usr/bin/env python
# -*- vim: set fileencoding=utf-8 -*-

import sys
import audiolabel
import subprocess

def test_initialization():
    l1 = audiolabel.Label('first', 1.0, 2.0)
    l2 = audiolabel.Label('second', 2.0, 3.0)
    l3 = audiolabel.Label('third', 3.0, 4.0)
    assert l1.text == 'first'
    assert l1.t1 == 1.0
    assert l1.t2 == 2.0
    t1 = audiolabel.IntervalTier(name='tier1')
    t1.add(l1)
    t1.add(l2)
    t1.add(l3)
    assert t1.label_at(2.5) == l2
    assert t1[0] == l1
    assert t1[-1] == l3
    lm = audiolabel.LabelManager()
    lm.add(t1)
    assert lm.tier('tier1') == t1
    assert t1.next(l1) == l2
    assert t1.next(l1, skip=1) == l3
    assert t1.prev(l3) == l2
    assert t1.prev(l3, skip=1) == l1

# Test reading of a Praat long TextGrid.
def test_praat_long():
    lm = audiolabel.LabelManager(
        from_file='test/this_is_a_label_file.long.TextGrid',
        from_type='praat_long'
    )
    assert len(lm._tiers) == 3
    assert lm.names == ('word', 'phone', 'stimulus')

# Test reading of a Praat long TextGrid with generic 'praat' from_type.
def test_praat_long_generic_fromtype():
    lm = audiolabel.LabelManager(
        from_file='test/this_is_a_label_file.long.TextGrid',
        from_type='praat'
    )
    assert len(lm._tiers) == 3
    assert lm.names == ('word', 'phone', 'stimulus')

# Test reading of a Praat short TextGrid.
def test_praat_short():
    lm = audiolabel.LabelManager(
        from_file='test/this_is_a_label_file.short.TextGrid',
        from_type='praat_short'
    )
    assert len(lm._tiers) == 3
    assert lm.names == ('word', 'phone', 'stimulus')

# Test reading of a Praat short TextGrid with generic 'praat' from_type.
def test_praat_short_generic_fromtype():
    lm = audiolabel.LabelManager(
        from_file='test/this_is_a_label_file.short.TextGrid',
        from_type='praat'
    )
    assert len(lm._tiers) == 3
    assert lm.names == ('word', 'phone', 'stimulus')

# Test that names, scale_by, shift_by params work.
def test_LabelManager_params():
    lm = audiolabel.LabelManager(
        from_file='test/this_is_a_label_file.short.TextGrid',
        from_type='praat'
    )
    assert len(lm._tiers) == 3
    assert lm.names == ('word', 'phone', 'stimulus')
    assert '{:0.4f}'.format(lm.tier(0)[1].t1) == '0.0453'
    lm = audiolabel.LabelManager(
        from_file='test/this_is_a_label_file.short.TextGrid',
        from_type='praat',
        names=['sec','rms','f1'],
        scale_by=100,
        shift_by=10
    )
    assert len(lm._tiers) == 3
    assert lm.names == ('sec', 'rms', 'f1')
    # shift_by is in the time units after scale_by is applied
    assert '{:0.4f}'.format(lm.tier(0)[1].t1) == '14.5320'

def test_praat_utf_8():
    lm = audiolabel.LabelManager(
        from_file='test/ipa.TextGrid',
        from_type='praat'
    )
    assert lm.tier('phone').label_at(0.6).text == u"ɯ"
    assert lm.tier('phone').label_at(0.7).text == u"ʤ"

def test_praat_utf_16_be():
    lm = audiolabel.LabelManager(
        from_file='test/Turkmen_NA_20130919_G_3.TextGrid',
        from_type='praat'
    )
    # TODO: add tests

def test_praat_utf_16_be_warn():
    sys.stderr.write('''The following two lines should be repeated after the asterisks:
WARNING: overriding user-specified encoding utf-8.
Found BOM for utf_16_be encoding.
***************
'''
    )
    lm = audiolabel.LabelManager(
        from_file='test/Turkmen_NA_20130919_G_3.TextGrid',
        from_type='praat',
        codec='utf-8'
    )
    # TODO: add tests. capture stderr and don't display at runtime

def test_praat_utf_8_no_bom():
    lm = audiolabel.LabelManager(
        from_file='test/utf8_no_BOM.TextGrid',
        from_type='praat',
        codec='utf-8'
    )
    assert lm.tier('s1').label_at(8.0).text == u"bet bít"
    assert lm.tier('s2').label_at(6.0).text == u"bat bat"

def test_esps():
    lm = audiolabel.LabelManager(
        from_file='test/sample.esps',
        from_type='esps'
    )
    assert len(lm._tiers) == 2
    assert lm.tier(0)[2].text == 'eh'
    assert lm.tier(1)[0].text == 'sat'

def test_table():
    lm = audiolabel.LabelManager(
        from_file='test/sample.table',
        from_type='table',
        fields_in_head=True,
        t1_col='sec'
    )
    assert len(lm._tiers) == 6
    assert lm.tier('rms')[0].text == '7.1'
    rms0 = lm.tier('rms')[0]
    assert lm.tier('rms').next(rms0).text == '7.4'
    assert lm.tier('rms').next(rms0, 2).text == '7.3'

def test_table_pipe():
    # First, create table from file.
    lm_file = audiolabel.LabelManager(
        from_file='test/pplain.table',
        from_type='table',
        sep=' ',
        fields_in_head=False,
        fields='f0,is_voiced,rms,acpeak',
        t1_col=None,
        t1_start=0.0,
        t1_step=0.010
    )
    assert len(lm_file._tiers) == 4
    assert lm_file.tier('rms')[0].text == '0'
    rms0 = lm_file.tier('rms')[0]
    assert lm_file.tier('rms').next(rms0).text == '28.0572'
    assert lm_file.tier('rms').next(rms0, 2).text == '47.6023'
    # Second, create table from same file and using subprocess.
    cat_proc = subprocess.Popen(
        ['cat', 'test/pplain.table'],
        stdout=subprocess.PIPE
    )
    lm_proc = audiolabel.LabelManager(
        from_file=cat_proc.stdout,
        from_type='table',
        sep=' ',
        fields_in_head=False,
        fields='f0,is_voiced,rms,acpeak',
        t1_col=None,
        t1_start=0.0,
        t1_step=0.010
    )
    assert len(lm_proc._tiers) == 4
    assert lm_proc.tier('rms')[0].text == '0'
    rms0 = lm_proc.tier('rms')[0]
    assert lm_proc.tier('rms').next(rms0).text == '28.0572'
    assert lm_proc.tier('rms').next(rms0, 2).text == '47.6023'
    # Third, make sure the results are the same.
    for name in lm_file.names:
        tier_file = lm_file.tier(name)
        tier_proc = lm_proc.tier(name)
        for (l_file, l_proc) in zip(tier_file, tier_proc):
            assert(l_file.t1 == l_proc.t1)
            assert(l_file.t2 == l_proc.t2)
            assert(l_file.text == l_proc.text)

def test_table_pipe_newlines():
    '''Test reading from table using subprocess with universal_newlines.'''
    cat_proc = subprocess.Popen(
        ['cat', 'test/pplain.table'],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    lm_proc = audiolabel.LabelManager(
        from_file=cat_proc.stdout,
        from_type='table',
        sep=' ',
        fields_in_head=False,
        fields='f0,is_voiced,rms,acpeak',
        t1_col=None,
        t1_start=0.0,
        t1_step=0.010
    )
    assert len(lm_proc._tiers) == 4
    assert lm_proc.tier('rms')[0].text == '0'
    rms0 = lm_proc.tier('rms')[0]
    assert lm_proc.tier('rms').next(rms0).text == '28.0572'
    assert lm_proc.tier('rms').next(rms0, 2).text == '47.6023'

def test_get_praat_header():
    lm = audiolabel.LabelManager(
        from_file='test/this_is_a_label_file.long.TextGrid',
        from_type='praat'
    )
    assert len(lm._tiers) == 3
    assert lm.names == ('word', 'phone', 'stimulus')

def test_tslice_incl():
    tier = audiolabel.IntervalTier()
    for t1 in (range(5)):
        tier.add(
            audiolabel.Label(
                t1=float(t1), t2=float(t1+1), text = 'label' + str(t1)
            )
        )
    s = tier.tslice(1.0, 4.0)
    assert(len(s) == 5)
    assert(s[0].text == 'label0')
    assert(s[-1].text == 'label4')
    s = tier.tslice(1.0, 4.0, lincl=False)
    assert(len(s) == 4)
    assert(s[0].text == 'label1')
    assert(s[-1].text == 'label4')
    s = tier.tslice(1.0, 4.0, rincl=False)
    assert(len(s) == 4)
    assert(s[0].text == 'label0')
    assert(s[-1].text == 'label3')
    s = tier.tslice(1.0, 4.0, lincl=False, rincl=False)
    assert(len(s) == 3)
    assert(s[0].text == 'label1')
    assert(s[-1].text == 'label3')

def test_tslice_strip():
    tier = audiolabel.IntervalTier()
    for t1 in (range(5)):
        tier.add(
            audiolabel.Label(
                t1=float(t1), t2=float(t1+1), text = 'label' + str(t1)
            )
        )
    s = tier.tslice(0.8, 4.2)
    assert(len(s) == 5)
    assert(s[0].text == 'label0')
    assert(s[-1].text == 'label4')
    s = tier.tslice(0.8, 4.2, lstrip=True)
    assert(len(s) == 4)
    assert(s[0].text == 'label1')
    assert(s[-1].text == 'label4')
    s = tier.tslice(0.8, 4.2, rstrip=True)
    assert(len(s) == 4)
    assert(s[0].text == 'label0')
    assert(s[-1].text == 'label3')
    s = tier.tslice(0.8, 4.2, lstrip=True, rstrip=True)
    assert(len(s) == 3)
    assert(s[0].text == 'label1')
    assert(s[-1].text == 'label3')

def test_tslice_tol():
    tier = audiolabel.IntervalTier()
    for t1 in (range(5)):
        tier.add(
            audiolabel.Label(
                t1=float(t1), t2=float(t1+1), text = 'label' + str(t1)
            )
        )
    s = tier.tslice(1.0001, 3.9999)
    assert(len(s) == 3)
    assert(s[0].text == 'label1')
    assert(s[-1].text == 'label3')
    s = tier.tslice(1.0001, 3.9999, tol=0.001)
    assert(len(s) == 5)
    assert(s[0].text == 'label0')
    assert(s[-1].text == 'label4')

if __name__ == '__main__':
    test_initialization()
    test_praat_long()
    test_praat_long_generic_fromtype()
    test_praat_short()
    test_praat_short_generic_fromtype()
    test_LabelManager_params()
    test_praat_utf_8()
    test_praat_utf_16_be()
    test_praat_utf_16_be_warn()
    test_praat_utf_8_no_bom()
    test_esps()
    test_table()
    test_table_pipe()
    test_table_pipe_newlines()
    test_get_praat_header()
    test_tslice_incl()
    test_tslice_strip()
    test_tslice_tol()
