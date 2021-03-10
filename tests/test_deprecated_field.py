import pytest

from .models import (
    Album,
    Musician,
    Label,
    warn_function,
)

from django.forms.models import modelform_factory


@pytest.fixture
def warn():
    warn_function.reset()
    return warn_function


@pytest.mark.django_db
def test_should_return_the_same_value_as_the_aliased_field():
    musician = Musician.objects.create(name="foo")
    assert musician.title == musician.name


@pytest.mark.django_db
def test_should_set_value_to_the_aliased_field():
    musician = Musician.objects.create(name="foo")
    musician.title = "bar"
    assert musician.name == "bar"


@pytest.mark.django_db
def test_should_warn_when_accessing_it(warn):
    musician = Musician.objects.create(name="foo")
    assert warn.counter == 0
    assert musician.title
    assert warn.counter == 1


@pytest.mark.django_db
def test_should_warn_when_setting_it(warn):
    musician = Musician.objects.create(name="foo")
    assert warn.counter == 0
    musician.title = "bar"
    assert warn.counter == 1


@pytest.mark.django_db
def test_should_warn_when_setting_it_while_creating(warn):
    Musician.objects.create(title="foo")
    assert warn.counter == 1


@pytest.mark.django_db
def test_should_work_as_a_filter_parameter_when_aliased_field_is_a_char_field():
    musician = Musician.objects.create(name="foo")
    search_musician = Musician.objects.filter(title="foo").first()
    assert search_musician == musician


@pytest.mark.django_db
def test_should_work_as_a_filter_parameter_when_aliased_field_is_a_foreign_field():
    musician = Musician.objects.create(name="foo")
    album = Album.objects.create(artist=musician)
    search_album = Album.objects.filter(musician=musician).first()
    assert search_album == album


@pytest.mark.django_db
def test_modelform_save_with_required(warn):
    form_class = modelform_factory(Label, fields="__all__")
    data = {"ticker": "BKFG"}
    form = form_class(data)
    assert form.fields["nyse"].widget.attrs == {"disabled": True}
    assert form.is_valid()
    res = form.save()
    assert res.ticker == "BKFG"
    assert warn.counter == 0
    assert res.nyse == "BKFG"
    assert warn.counter == 1


@pytest.mark.django_db
def test_modelform_update_via_aliased_with_required(warn):
    existing = Label.objects.create(ticker="old_ticker")
    form_class = modelform_factory(Label, fields="__all__")

    data = {"ticker": "BKFG"}
    form = form_class(data, instance=existing)
    # This warning check caught an issue with model_to_dict()
    assert warn.counter == 0
    assert form.is_valid()
    res = form.save()

    # make sure none of the form actions triggered a warning, either
    assert warn.counter == 0
    assert res.ticker == "BKFG"
    assert res.nyse == "BKFG"
    assert warn.counter == 1  # only legit warning
