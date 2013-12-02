import audiolabel

# Test reading of a Praat long TextGrid.
def test_praat_long():
    lm = audiolabel.LabelManager(
        fromFile='test/this_is_a_label_file.long.TextGrid',
        fromType='praat_long'
    )
    assert len(lm._tiers) == 3
    assert lm.names() == ('word', 'phone', 'stimulus')

# Test reading of a Praat long TextGrid with generic 'praat' fromType.
def test_praat_long_generic_fromtype():
    lm = audiolabel.LabelManager(
        fromFile='test/this_is_a_label_file.long.TextGrid',
        fromType='praat'
    )
    assert len(lm._tiers) == 3
    assert lm.names() == ('word', 'phone', 'stimulus')

# Test reading of a Praat short TextGrid.
def test_praat_short():
    lm = audiolabel.LabelManager(
        fromFile='test/this_is_a_label_file.short.TextGrid',
        fromType='praat_short'
    )
    assert len(lm._tiers) == 3
    assert lm.names() == ('word', 'phone', 'stimulus')

# Test reading of a Praat short TextGrid with generic 'praat' fromType.
def test_praat_short_generic_fromtype():
    lm = audiolabel.LabelManager(
        fromFile='test/this_is_a_label_file.short.TextGrid',
        fromType='praat'
    )

def test_praat_utf_8():
    lm = audiolabel.LabelManager(
        fromFile='test/ipa.TextGrid',
        fromType='praat'
    )

def test_praat_utf_16_be():
    lm = audiolabel.LabelManager(
        fromFile='test/Turkmen_NA_20130919_G_3.TextGrid',
        fromType='praat'
    )

def test_esps():
    lm = audiolabel.LabelManager(
        fromFile='test/sample.esps',
        fromType='esps'
    )

def test_get_praat_header():
    lm = audiolabel.LabelManager(
        fromFile='test/this_is_a_label_file.long.TextGrid',
        fromType='praat'
    )
    assert len(lm._tiers) == 3
    assert lm.names() == ('word', 'phone', 'stimulus')
    #lm._getPraatHeader()


