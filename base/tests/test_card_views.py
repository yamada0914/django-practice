import pytest


@pytest.mark.django_db
def test_index_view_only_lists_published_cards(client, published_card, unpublished_card):
    response = client.get("/")
    assert response.status_code == 200

    listed_cards = list(response.context["object_list"])
    assert published_card in listed_cards
    assert unpublished_card not in listed_cards


@pytest.mark.django_db
def test_card_detail_view_returns_card_context(client, published_card):
    response = client.get(f"/products/{published_card.pk}/")
    assert response.status_code == 200
    assert response.context["object"].pk == published_card.pk


@pytest.mark.django_db
def test_tag_list_filters_cards_by_tag(client, published_card, tag):
    response = client.get(f"/tags/{tag.slug}/")
    assert response.status_code == 200

    listed_cards = list(response.context["object_list"])
    assert published_card in listed_cards
