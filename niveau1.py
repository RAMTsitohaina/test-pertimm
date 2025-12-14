"""
Test Technique Pertimm - Niveau 1
Automatisation des interactions avec l'API Concrete-datastore
"""

import requests
import time
from typing import Dict, Optional
import json


class PertimmAPIClient:
    """Client pour interagir avec l'API Pertimm hire-game."""

    BASE_URL = "https://hire-game.pertimm.dev"
    
    def __init__(self):
        """Initialise le client API."""
        self.token: Optional[str] = None
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Retourne les en-têtes HTTP avec le token d'authentification.
        
        Returns:
            Dictionnaire contenant les en-têtes HTTP
        """
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        return headers
    
    def register(
        self, 
        email: str, 
        password: str,
        first_name: str,
        last_name: str
    ) -> Dict:
        """
        Enregistre un nouvel utilisateur dans l'API.
        
        Args:
            email: Adresse email de l'utilisateur
            password: Mot de passe de l'utilisateur
            first_name: Prénom de l'utilisateur (optionnel)
            last_name: Nom de l'utilisateur (optionnel)
            
        Returns:
            Réponse JSON de l'API
        """
        url = f"{self.BASE_URL}/api/v1.1/auth/register/"
        data = {
            "email": email,
            "password1": password,
            "password2": password,
            "first_name": first_name,
            "last_name": last_name
        }
        
        print("Charge utile envoyée (JSON) :")
        print(json.dumps(data, indent=4))
        
        try:
            response = self.session.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()

            try:
                response_data = response.json()
                print("Corps de la réponse JSON :")
                print(json.dumps(response_data, indent=4))
            except json.JSONDecodeError:
                print("Corps de la réponse (non-JSON) :")
                print(response.text)
                response_data = None
                
            # 4. Gestion des codes de statut
            if response.status_code in (200, 201):
                print("\n✅ Enregistrement RÉUSSI. Vérifiez l'e-mail pour la confirmation (si nécessaire).")
                # Le token d'authentification est dans la réponse
                if response_data and response_data.get("token"):
                    print(f"Jeton d'authentification reçu : {response_data['token'][:20]}...")
                return response_data
            
            elif 400 <= response.status_code < 600:
                print("\n❌ ERREUR : L'enregistrement a échoué. Vérifiez les détails de l'erreur ci-dessus.")
                return None
        except requests.exceptions.RequestException as e:
            # Cette erreur apparaît si le problème ConnectionError/DNS n'est pas résolu
            print(f"\n❌ ERREUR MAJEURE DE CONNEXION : {e}")
            print("Veuillez vérifier votre connexion Internet et l'orthographe du BASE_URL.")
            return None
    
    def login(self, email: str, password: str) -> str:
        """
        Connecte l'utilisateur et récupère le token d'authentification.
        
        Args:
            email: Adresse email de l'utilisateur
            password: Mot de passe de l'utilisateur
            
        Returns:
            Token d'authentification
        """
        url = f"{self.BASE_URL}/api/v1.1/auth/login/"
        data = {"email": email, "password": password}
        
        try:
            response = self.session.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            self.token = result.get("token")
            return self.token
        except requests.exceptions.RequestException as e:
            print(f"\n❌ ERREUR DE CONNEXION : {e}")
            return None
    
    def create_application(
        self, 
        email: str, 
        first_name: str, 
        last_name: str
    ) -> Dict:
        """
        Crée une demande d'application.
        
        Args:
            email: Adresse email du candidat
            first_name: Prénom du candidat
            last_name: Nom du candidat
            
        Returns:
            Réponse JSON contenant l'URL de suivi
        """
        url = f"{self.BASE_URL}/api/v1.1/job-application-request/"
        data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name
        }
        
        response = self.session.post(url, json=data, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, status_url: str, timeout: int = 30) -> Dict:
        """
        Attend que le statut de l'application soit COMPLETED.
        
        Args:
            status_url: URL pour vérifier le statut
            timeout: Temps maximum d'attente en secondes
            
        Returns:
            Réponse JSON finale avec confirmation_url
        """
        start_time = time.time()
        check_interval = 0.5  # Vérifie toutes les 0.5 secondes
        
        while time.time() - start_time < timeout:
            response = self.session.get(
                status_url, 
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            status = result.get("status")
            
            print(f"   Status actuel: {status}")
            
            if status == "COMPLETED":
                return result
            
            time.sleep(check_interval)
        
        raise TimeoutError(
            f"L'application n'a pas été complétée dans les {timeout} secondes"
        )
    
    def confirm_application(self, confirmation_url: str) -> Dict:
        """
        Confirme l'application en envoyant une requête PATCH.
        
        Args:
            confirmation_url: URL de confirmation
            
        Returns:
            Réponse JSON de confirmation
        """
        data = {"confirmed": True}
        
        response = self.session.patch(
            confirmation_url, 
            json=data, 
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()


def main():
    """Fonction principale pour exécuter le test technique."""
    # Configuration - MODIFIEZ CES VALEURS
    EMAIL = "tsitoramangaso@gmail.com"
    PASSWORD = "mdp123456"
    FIRST_NAME = "Tsitohaina"
    LAST_NAME = "Ramangason"
    
    print("=== Test Technique Pertimm - Niveau 1 ===\n")
    
    client = PertimmAPIClient()
    
    try:            
        # Étape 1: Enregistrement
        if not client.token:
            print("1. Enregistrement...")
            try:
                result = client.register(EMAIL, PASSWORD, FIRST_NAME, LAST_NAME)
                print(f"   ✓ Enregistrement réussi")
                print(f"   ✓ Token reçu: {client.token[:20] if client.token else 'N/A'}...")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400:
                    print("   ⚠ Utilisateur déjà enregistré, passage au login")
                else:
                    raise
        
            # Étape 2: Connexion (si pas de token après l'enregistrement)
            if not client.token:
                print("\n2. Connexion...")
                token = client.login(EMAIL, PASSWORD)
                print(f"   ✓ Connexion réussie - Token: {token[:20]}...")
            else:
                print("\n2. Connexion (sautée car token déjà obtenu)")
        
        # Étape 3: Création de l'application
        print("\n3. Création de l'application...")
        start_time = time.time()
        
        app_response = client.create_application(EMAIL, FIRST_NAME, LAST_NAME)
        status_url = app_response.get("url")
        print(f"   ✓ Application créée")
        print(f"   ✓ URL de suivi: {status_url}")
        
        # Étape 4: Attente de la complétion
        print("\n4. Attente de la complétion...")
        completed_response = client.wait_for_completion(status_url, timeout=25)
        confirmation_url = completed_response.get("confirmation_url")
        print(f"   ✓ Application complétée!")
        print(f"   ✓ URL de confirmation: {confirmation_url}")
        
        # Étape 5: Confirmation (dans les 30 secondes)
        elapsed_time = time.time() - start_time
        print(f"\n5. Confirmation (temps écoulé: {elapsed_time:.1f}s)...")
        
        if elapsed_time >= 30:
            print("   ✗ ERREUR: Plus de 30 secondes écoulées!")
            return
        
        confirmation_response = client.confirm_application(confirmation_url)
        print("   ✓ Application confirmée avec succès!")
        print(f"\n   Réponse finale:")
        for key, value in confirmation_response.items():
            print(f"      {key}: {value}")
        
        print("\n" + "="*50)
        print("✓✓✓ TEST TERMINÉ AVEC SUCCÈS! ✓✓✓")
        print("="*50)
        
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ Erreur HTTP {e.response.status_code}: {e.response.text}")
        raise
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        raise


if __name__ == "__main__":
    main()