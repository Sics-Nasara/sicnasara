from django.test import TestCase, Client
from django.urls import reverse
from scuelo.models import AnneeScolaire, Classe, Eleve, Inscription

class PromotionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Setup test data for classes, years, students, inscriptions


    def test_get_promotion_page(self):
        url = reverse('manage_promotions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('classes', response.context)
        self.assertIn('annee_scolaires', response.context)


    def test_post_promotion(self):
        url = reverse('manage_promotions')
        from_class = Classe.objects.get(nom='GS').id
        to_class = Classe.objects.get(nom='CP1').id
        next_year = AnneeScolaire.objects.get(actuel=False).id

        response = self.client.post(url, data={
            'from_class': from_class,
            'to_class': to_class,
            'annee_scolaire': next_year,
        })

        self.assertRedirects(response, url)
        # Additional asserts can check that inscriptions were created correctly
