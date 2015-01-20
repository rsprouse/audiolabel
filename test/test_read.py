#!/usr/bin/env python
# -*- vim: set fileencoding=utf-8 -*-

import audiolabel

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
    # TODO: add test

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

def test_get_praat_header():
    lm = audiolabel.LabelManager(
        from_file='test/this_is_a_label_file.long.TextGrid',
        from_type='praat'
    )
    assert len(lm._tiers) == 3
    assert lm.names == ('word', 'phone', 'stimulus')


if __name__ == '__main__':
    test_initialization()
    test_praat_long()
    test_praat_long_generic_fromtype()
    test_praat_short()
    test_praat_short_generic_fromtype()
    test_praat_utf_8()
    test_praat_utf_16_be()
    test_esps()
    test_table()
    test_get_praat_header()
