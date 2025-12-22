#!/usr/bin/env python3
"""
Utilitaire pour générer et gérer les mots de passe admin
Usage: python admin_password_tool.py
"""

import hashlib
import getpass
import sys
from pathlib import Path


def generate_hash(password: str, algorithm: str = 'sha256') -> str:
    """Génère un hash pour un mot de passe"""
    return hashlib.new(algorithm, password.encode()).hexdigest()


def verify_hash(password: str, hash_value: str, algorithm: str = 'sha256') -> bool:
    """Vérifie qu'un mot de passe correspond à un hash"""
    return generate_hash(password, algorithm) == hash_value


def interactive_mode():
    """Mode interactif pour générer ou vérifier un hash"""
    print("=" * 60)
    print("  Illama Launcher - Gestionnaire de mot de passe admin")
    print("=" * 60)
    print()
    
    print("Que veux-tu faire ?")
    print("1. Générer un nouveau hash")
    print("2. Vérifier un mot de passe contre un hash")
    print("3. Mettre à jour .env automatiquement")
    print("4. Quitter")
    print()
    
    choice = input("Ton choix (1-4) : ").strip()
    print()
    
    if choice == '1':
        generate_new_hash()
    elif choice == '2':
        verify_existing_hash()
    elif choice == '3':
        update_env_file()
    elif choice == '4':
        print("Au revoir !")
        sys.exit(0)
    else:
        print("❌ Choix invalide !")
        sys.exit(1)


def generate_new_hash():
    """Génère un nouveau hash de mot de passe"""
    print("🔐 Génération d'un nouveau hash de mot de passe")
    print("-" * 60)
    
    # Demander le mot de passe (masqué)
    password = getpass.getpass("Entre ton mot de passe admin : ")
    
    if not password:
        print("❌ Mot de passe vide !")
        sys.exit(1)
    
    # Confirmer le mot de passe
    password_confirm = getpass.getpass("Confirme le mot de passe : ")
    
    if password != password_confirm:
        print("❌ Les mots de passe ne correspondent pas !")
        sys.exit(1)
    
    # Générer le hash
    hash_value = generate_hash(password)
    
    print()
    print("✅ Hash généré avec succès !")
    print()
    print("=" * 60)
    print(f"Hash SHA-256 :")
    print(hash_value)
    print("=" * 60)
    print()
    print("📝 Ajoute cette ligne dans ton fichier .env :")
    print()
    print(f"ADMIN_PASSWORD_HASH={hash_value}")
    print()
    
    # Proposer de copier dans le presse-papier (si pyperclip est installé)
    try:
        import pyperclip
        pyperclip.copy(hash_value)
        print("📋 Hash copié dans le presse-papier !")
        print()
    except ImportError:
        print("💡 Astuce : Installe 'pyperclip' pour copier automatiquement")
        print("   pip install pyperclip")
        print()


def verify_existing_hash():
    """Vérifie un mot de passe contre un hash existant"""
    print("🔍 Vérification d'un mot de passe")
    print("-" * 60)
    
    # Demander le hash
    hash_value = input("Entre le hash SHA-256 à vérifier : ").strip()
    
    if not hash_value or len(hash_value) != 64:
        print("❌ Hash invalide ! (doit être 64 caractères hexadécimaux)")
        sys.exit(1)
    
    # Demander le mot de passe
    password = getpass.getpass("Entre le mot de passe à vérifier : ")
    
    if not password:
        print("❌ Mot de passe vide !")
        sys.exit(1)
    
    # Vérifier
    if verify_hash(password, hash_value):
        print()
        print("✅ CORRECT ! Le mot de passe correspond au hash.")
        print()
    else:
        print()
        print("❌ INCORRECT ! Le mot de passe ne correspond pas au hash.")
        print()


def update_env_file():
    """Met à jour automatiquement le fichier .env"""
    print("📝 Mise à jour du fichier .env")
    print("-" * 60)
    
    env_path = Path('.env')
    
    # Vérifier si .env existe
    if not env_path.exists():
        print("⚠️  Le fichier .env n'existe pas.")
        create = input("Veux-tu le créer depuis .env.example ? (o/n) : ").strip().lower()
        
        if create == 'o':
            example_path = Path('.env.example')
            if not example_path.exists():
                print("❌ .env.example non trouvé !")
                sys.exit(1)
            
            # Copier .env.example vers .env
            import shutil
            shutil.copy(example_path, env_path)
            print("✅ .env créé depuis .env.example")
        else:
            print("❌ Opération annulée")
            sys.exit(1)
    
    # Demander le nouveau mot de passe
    password = getpass.getpass("Entre le nouveau mot de passe admin : ")
    
    if not password:
        print("❌ Mot de passe vide !")
        sys.exit(1)
    
    password_confirm = getpass.getpass("Confirme le mot de passe : ")
    
    if password != password_confirm:
        print("❌ Les mots de passe ne correspondent pas !")
        sys.exit(1)
    
    # Générer le hash
    hash_value = generate_hash(password)
    
    # Lire le contenu de .env
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Chercher et remplacer la ligne ADMIN_PASSWORD_HASH
    found = False
    for i, line in enumerate(lines):
        if line.startswith('ADMIN_PASSWORD_HASH='):
            lines[i] = f'ADMIN_PASSWORD_HASH={hash_value}\n'
            found = True
            break
    
    # Si pas trouvé, ajouter à la fin
    if not found:
        lines.append(f'\nADMIN_PASSWORD_HASH={hash_value}\n')
    
    # Écrire le fichier
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print()
    print("✅ Fichier .env mis à jour avec succès !")
    print()
    print("🔐 Le nouveau hash a été configuré :")
    print(f"   {hash_value}")
    print()


def main():
    """Point d'entrée principal"""
    # Mode ligne de commande
    if len(sys.argv) > 1:
        if sys.argv[1] == '--generate' or sys.argv[1] == '-g':
            if len(sys.argv) > 2:
                password = sys.argv[2]
                hash_value = generate_hash(password)
                print(hash_value)
            else:
                print("Usage: python admin_password_tool.py --generate 'ton_mot_de_passe'")
                sys.exit(1)
        elif sys.argv[1] == '--verify' or sys.argv[1] == '-v':
            if len(sys.argv) > 3:
                password = sys.argv[2]
                hash_value = sys.argv[3]
                if verify_hash(password, hash_value):
                    print("✅ MATCH")
                    sys.exit(0)
                else:
                    print("❌ NO MATCH")
                    sys.exit(1)
            else:
                print("Usage: python admin_password_tool.py --verify 'mot_de_passe' 'hash'")
                sys.exit(1)
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("Usage:")
            print("  python admin_password_tool.py                    # Mode interactif")
            print("  python admin_password_tool.py -g 'password'      # Générer un hash")
            print("  python admin_password_tool.py -v 'pass' 'hash'   # Vérifier")
            sys.exit(0)
        else:
            print("Option inconnue. Utilise --help pour l'aide.")
            sys.exit(1)
    else:
        # Mode interactif
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print("\n\n⚠️  Opération annulée par l'utilisateur")
            sys.exit(0)


if __name__ == "__main__":
    main()
