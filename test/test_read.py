import audiolabel

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

def test_praat_utf_8():
    lm = audiolabel.LabelManager(
        from_file='test/ipa.TextGrid',
        from_type='praat'
    )

def test_praat_utf_16_be():
    lm = audiolabel.LabelManager(
        from_file='test/Turkmen_NA_20130919_G_3.TextGrid',
        from_type='praat'
    )

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
    test_praat_long()
    test_praat_long_generic_fromtype()
    test_praat_short()
    test_praat_short_generic_fromtype()
    test_praat_utf_8()
    test_praat_utf_16_be()
    test_esps()
    test_table()
    test_get_praat_header()
