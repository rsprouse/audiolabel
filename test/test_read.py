#!/usr/bin/env python
# -*- vim: set fileencoding=utf-8 -*-

import os, sys
from tempfile import NamedTemporaryFile
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
    assert t1.end == 4.0

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

# Test reading of a Praat long TextGrid with empty tiers.
def test_praat_long_empty_tier():
    lm = audiolabel.LabelManager(
        from_file='test/empty_tier.long.TextGrid',
        from_type='praat'
    )
    assert len(lm._tiers) == 5
    assert lm.names == (
        'V1','empty_point_1','empty_interval','V2','empty_point_end'
    )
    assert(len(lm.tier('V1')) == 3)
    assert(len(lm.tier('empty_point_1')) == 0)
    assert(len(lm.tier('empty_interval')) == 0)
    assert(len(lm.tier('V2')) == 4)
    assert(len(lm.tier('empty_point_end')) == 0)

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

# Test reading of a Praat short TextGrid with empty tiers.
def test_praat_short_empty_tier():
    lm = audiolabel.LabelManager(
        from_file='test/empty_tier.short.TextGrid',
        from_type='praat'
    )
    assert len(lm._tiers) == 5
    assert lm.names == (
        'V1','empty_point_1','empty_interval','V2','empty_point_end'
    )
    assert(len(lm.tier('V1')) == 3)
    assert(len(lm.tier('empty_point_1')) == 0)
    assert(len(lm.tier('empty_interval')) == 0)
    assert(len(lm.tier('V2')) == 4)
    assert(len(lm.tier('empty_point_end')) == 0)

# Test reading of a Praat short TextGrid with multiline labels.
def test_praat_short_multiline():
    lm = audiolabel.LabelManager(
        from_file='test/multiline.short.TextGrid',
        from_type='praat'
    )
    assert len(lm._tiers) == 1
    assert(len(lm.tier('multiline')) == 11)
    texts = ['', 'a', 'b\n', 'c\n', '"', '1', '""', '"\n', '""\n', '', '""\n"']
    mtier = lm.tier('multiline')
    for idx, text in enumerate(texts):
        assert(mtier[idx].text == text)

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

def test_names_property():
    lm = audiolabel.LabelManager(
        from_file='test/this_is_a_label_file.short.TextGrid',
        from_type='praat'
    )
    assert lm.names == ('word', 'phone', 'stimulus')
    lm.names = ['sec','rms']
    assert lm.names == ('sec', 'rms', 'stimulus')
    lm.names = [None,'two']
    assert lm.names == ('sec', 'two', 'stimulus')
    lm.names = ['one','two','three']
    assert lm.names == ('one', 'two', 'three')

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

def test_eaf():
    lm = audiolabel.LabelManager(
        from_file='test/v2test.eaf',
        from_type='eaf'
    )
    assert len(lm._tiers) == 22
    assert lm.tier('A_Transcription')[2].text == 'áas'
    assert lm.tier('A_Transcription')[2].t1 == 188675.0
    assert lm.tier('A_Translation')[2].text == 'bowl'
    assert lm.tier('A_Translation')[2].t1 == 188675.0

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

def test_as_string_praat_short():
    '''Test output of as_string(). Make sure to handle quotation marks.'''
    lm = audiolabel.LabelManager(
        from_file='test/quotes.TextGrid',
        from_type='praat'
    )
    s = 'File type = "ooTextFile"\nObject class = "TextGrid"\n\n0.00000000000000000000\n1.00000000000000000000\n<exists>\n2\n"IntervalTier"\n"interval"\n0.000000000000\n1.000000000000\n2\n0.00000000000000000000\n0.50000000000000000000\n"""a\'b\'c""d e"""\n0.50000000000000000000\n1.00000000000000000000\n""\n"TextTier"\n"point"\n0.000000000000\n1.000000000000\n1\n0.50000000000000000000\n"""a\'b\'c""d e"""'
    assert s == lm.as_string('praat_short')

def test_as_string_praat_long():
    '''Test output of as_string(). Make sure to handle quotation marks.'''
    lm = audiolabel.LabelManager(
        from_file='test/quotes.TextGrid',
        from_type='praat'
    )
    s = 'File type = "ooTextFile"\nObject class = "TextGrid"\n\nxmin = 0.00000000000000000000\nxmax = 1.00000000000000000000\ntiers? <exists>\nsize = 2\nitem []:\n    item [1]:\n        class = "IntervalTier"\n        name = "interval"\n        xmin = 0.000000000000\n        xmax = 1.000000000000\n        intervals: size = 2\n        intervals [1]:\n            xmin = 0.00000000000000000000\n            xmax = 0.50000000000000000000\n            text = """a\'b\'c""d e"""\n        intervals [2]:\n            xmin = 0.50000000000000000000\n            xmax = 1.00000000000000000000\n            text = ""\n    item [2]:\n        class = "TextTier"\n        name = "point"\n        xmin = 0.000000000000\n        xmax = 1.000000000000\n        points: size = 1\n        points [1]:\n            number = 0.50000000000000000000\n            mark = """a\'b\'c""d e"""'
    assert s == lm.as_string('praat_long')

def test_read_label():
    '''Test read_label() function.'''
    [phdf, wddf, ctxtdf] = audiolabel.read_label(
        'test/this_is_a_label_file.TextGrid', 'praat'
    )
    assert((wddf.columns == ['t1', 't2', 'label', 'fname']).all())
    assert(wddf.shape == (6, 4))
    assert(wddf.label[1] == 'IS')
    assert(ctxtdf.shape == (3, 4))
    assert(ctxtdf.label[1] == 'sad')
    assert(phdf.shape == (15, 4))
    assert(phdf.label[2] == 'S')

def test_read_label_tiers():
    '''Test tiers parameter of read_label().'''
    [phdf, wddf, ctxtdf] = audiolabel.read_label(
        'test/this_is_a_label_file.TextGrid', 'praat', tiers=['phone', 'word', 2]
    )
    assert((wddf.columns == ['t1', 't2', 'word', 'fname']).all())
    assert(wddf.shape == (6, 4))
    assert(wddf.word[1] == 'IS')
    assert((phdf.columns == ['t1', 't2', 'phone', 'fname']).all())
    assert(phdf.shape == (15, 4))
    assert(phdf.phone[2] == 'S')
    assert((ctxtdf.columns == ['t1', 't2', 'label', 'fname']).all())
    assert(ctxtdf.shape == (3, 4))
    assert(ctxtdf.label[1] == 'sad')

def test_read_label_list():
    '''Test reading a list of files.'''
    [wddf] = audiolabel.read_label(
        [
            'test/this_is_a_label_file.TextGrid',
            'test/Turkmen_NA_20130919_G_3.TextGrid'
        ],
        'praat',
        tiers=['word']
    )
    assert((wddf.columns == ['t1', 't2', 'word', 'fname']).all())
    assert(wddf.shape == (177, 4))
    assert(wddf.word[1] == 'IS')

def test_read_label_from_eaf():
    '''Some textgrids exported from ELAN appear to be valid (Praat can open
them), even though they differ in some details from the long textgrids created
by Praat. Make sure these can be read correctly.'''
    [df] = audiolabel.read_label('test/from_eaf.long.TextGrid', 'praat')
    assert((df.columns == ['t1', 't2', 'label', 'fname']).all())
    assert(df.shape == (6, 4))
    assert(df.label[0] == 'asdfasf')
    assert(df.label[4] == 'text')

def _test_df2tg_praat(df2tgfmt):
    '''Test output format for df2tg.'''
    [wddf, phdf, stdf] = audiolabel.read_label(
        'test/this_is_a_label_file.short.TextGrid', 'praat_short',
        tiers=['word', 'phone', 'stimulus']
    )
    tg = audiolabel.df2tg(
        [wddf, phdf, stdf],
        ['word', 'phone', 'stimulus'],
        t2=['t2', 't2', None],
        ftype=df2tgfmt
    )
    temp = NamedTemporaryFile('w+', delete=False)
    temp.write(tg)
    temp.close()
    try:
        [wddf2, phdf2, stdf2] = audiolabel.read_label(
            temp.name, df2tgfmt,
            tiers=['word', 'phone', 'stimulus']
        )
    finally:
        os.unlink(temp.name)
    assert(wddf2.loc[1, 'word'] == 'This')
    assert(wddf2.loc[4, 'word'] == 'label')
    assert(phdf2.loc[2, 'phone'] == 'IH')
    assert(phdf2.loc[5, 'phone'] == 'Z')
    assert(stdf2.loc[0, 'stimulus'] == '1')
    assert(stdf2.loc[2, 'stimulus'] == '3')

def test_df2tg_praat_short():
    '''Test praat_short output format for df2tg.'''
    _test_df2tg_praat('praat_short')

def test_df2tg_praat_long():
    '''Test praat_long output format for df2tg.'''
    _test_df2tg_praat('praat_long')

if __name__ == '__main__':
    test_initialization()
    test_praat_long()
    test_praat_long_generic_fromtype()
    test_praat_long_empty_tier()
    test_praat_short()
    test_praat_short_generic_fromtype()
    test_praat_short_empty_tier()
    test_praat_short_multiline()
    test_LabelManager_params()
    test_names_property()
    test_praat_utf_8()
    test_praat_utf_16_be()
    test_praat_utf_16_be_warn()
    test_praat_utf_8_no_bom()
    test_eaf()
    test_esps()
    test_table()
    test_table_pipe()
    test_table_pipe_newlines()
    test_get_praat_header()
    test_tslice_incl()
    test_tslice_strip()
    test_tslice_tol()
    test_as_string_praat_short()
    test_as_string_praat_long()
    test_read_label()
    test_read_label_tiers()
    test_read_label_list()
    test_read_label_from_eaf()
    test_df2tg_praat_short()
    test_df2tg_praat_long()
