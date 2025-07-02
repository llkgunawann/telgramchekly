import json
from datetime import datetime
import os
import sys

def load_json_file(path):
    """
    Memuat data dari file JSON. Mengembalikan None jika file tidak ditemukan atau kosong.
    """
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def get_users_with_info_from_followers(data):
    """Mengekstrak username dan timestamp dari data followers."""
    users_info = []
    if isinstance(data, list):
        for item in data:
            if "string_list_data" in item:
                for entry in item["string_list_data"]:
                    username = entry.get("value")
                    timestamp = entry.get("timestamp")
                    if username:
                        users_info.append({'username': username, 'timestamp': timestamp})
    elif isinstance(data, dict) and "string_list_data" in data:
        for entry in data["string_list_data"]:
            username = entry.get("value")
            timestamp = entry.get("timestamp")
            if username:
                users_info.append({'username': username, 'timestamp': timestamp})
    return users_info

def get_users_with_info_from_following(data):
    """Mengekstrak username dan timestamp dari data following."""
    users_info = []
    for item in data.get('relationships_following', []):
        for entry in item.get('string_list_data', []):
            username = entry.get('value')
            timestamp = entry.get('timestamp')
            if username:
                users_info.append({'username': username, 'timestamp': timestamp})
    return users_info

def check_follow_status(followers_path, following_path):
    """Membandingkan daftar following dan followers untuk menentukan status follow-back."""
    followers_data = load_json_file(followers_path)
    following_data = load_json_file(following_path)

    if followers_data is None or following_data is None:
        return None

    followers_info = get_users_with_info_from_followers(followers_data)
    following_info = get_users_with_info_from_following(following_data)
    
    followers_usernames = {user['username'] for user in followers_info}
    
    # Urutkan berdasarkan waktu follow, dari yang terbaru
    following_info.sort(key=lambda x: x['timestamp'] if x['timestamp'] is not None else 0, reverse=True)

    result_list = []
    for followed_user in following_info:
        username = followed_user['username']
        timestamp = followed_user['timestamp']
        
        is_following_back = username in followers_usernames
        status_symbol = "✅" if is_following_back else "❌"
        
        time_info = "Tanggal tidak tersedia"
        if timestamp:
            time_info = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        result_list.append({
            'username': username,
            'status': status_symbol,
            'followed_since': time_info,
            'is_following_back': is_following_back
        })

    return result_list

def print_categorized_report(all_following_status, my_username):
    """
    Mencetak laporan yang mengelompokkan akun menjadi 'following back' dan 'not following back'.
    """
    # Pisahkan daftar menjadi dua kategori berdasarkan status follow-back
    followers_back = [user for user in all_following_status if user['is_following_back']]
    unfollowers = [user for user in all_following_status if not user['is_following_back']]

    print("\n" + "=" * 60)
    print(f"Laporan Status Follow-Back untuk Akun: {my_username}")
    print("  (Diurutkan berdasarkan status, kemudian waktu follow terbaru)")
    print("=" * 60)
    print(f"{'Status':<10} | {'Username':<30} | {'Waktu Follow'}")
    print("-" * 60)

    # 1. Tampilkan daftar AKUN YANG MENGIKUTI ANDA KEMBALI (FOLLOW BACK)
    print("\n--- AKUN YANG MENGIKUTI ANDA KEMBALI (FOLLOW BACK) ---")
    if not followers_back:
        print(f"{'':<10} | {'Tidak ada akun yang mengikuti Anda kembali.':<30} |")
    else:
        for user_data in followers_back:
            print(f"{user_data['status']:<10} | {user_data['username']:<30} | {user_data['followed_since']}")

    # 2. Tampilkan daftar AKUN YANG TIDAK MENGIKUTI ANDA KEMBALI (UNFOLLOWERS)
    print("\n--- AKUN YANG TIDAK MENGIKUTI ANDA KEMBALI (UNFOLLOWERS) ---")
    if not unfollowers:
        print(f"{'':<10} | {'Semua akun yang Anda follow, follow Anda kembali.':<30} |")
    else:
        for user_data in unfollowers:
            print(f"{user_data['status']:<10} | {user_data['username']:<30} | {user_data['followed_since']}")
    
    print("\n" + "-" * 60)
    print(f"Total akun yang kamu follow: {len(all_following_status)}")
    print(f"Total akun yang mengikuti kamu kembali: {len(followers_back)}")
    print(f"Total unfollowers: {len(unfollowers)}")
    print("=" * 60)

def show_download_instructions():
    """Mencetak petunjuk cara mengunduh data Instagram."""
    print("\n⚠️ File data JSON tidak ditemukan.")
    print("Untuk melakukan pengecekan, kamu perlu mengunduh data Instagram-mu.")
    print("Ikuti langkah-langkah sederhana ini:")
    print("1. Buka aplikasi Instagram > Profil > Pengaturan (Settings) > Keamanan (Security) > Unduh Data (Download Data).")
    print("2. Masukkan alamat emailmu dan pilih format 'JSON'.")
    print("3. Tunggu email dari Instagram dan unduh datanya.")
    print(f"4. Ekstrak file zip, lalu pindahkan 'followers_1.json' dan 'following.json' ke dalam direktori ini: {os.getcwd()}.")
    print("\nSetelah file siap, jalankan ulang skrip ini.")

def run_check_and_report(username, followers_path, following_path):
    """
    Menjalankan pengecekan follow-back, menampilkan laporan, dan mengembalikan data hasil.
    """
    print("\nMemulai pengecekan menggunakan file lokal...")
    all_following_status = check_follow_status(followers_path, following_path)
    if all_following_status:
        # Panggil fungsi yang menampilkan hasil yang dikelompokkan
        print_categorized_report(all_following_status, username) 
        return all_following_status # Mengembalikan data hasil lengkap untuk fitur pencarian
    else:
        print("\n✅ Semua akun yang kamu follow juga follow kamu balik.")
        print("Atau terjadi masalah saat memuat data dari file. Pastikan filenya valid.")
        return None

def check_dependencies():
    """Memeriksa apakah library yang dibutuhkan sudah terpasang."""
    try:
        import requests
        print("✅ Library 'requests' sudah terpasang.")
    except ImportError:
        print("\n❌ Library 'requests' belum terpasang.")
        print("   Silakan install dengan perintah:")
        print("   >>> pip install requests")
        print("\n   Setelah selesai, jalankan ulang skrip.")
        sys.exit()

def search_by_username_feature(report_data):
    """Memungkinkan pengguna untuk mencari status follow-back dari username tertentu."""
    print("\n" + "=" * 60)
    print("🎉 Fitur: Cari Status Follow-Back berdasarkan Username")
    print("=" * 60)
    while True:
        search_query = input("Masukkan username yang ingin Anda cari (atau 'keluar' untuk kembali): ").strip()
        if search_query.lower() == 'keluar':
            break
        
        found_user = None
        for user_info in report_data:
            if user_info['username'].lower() == search_query.lower():
                found_user = user_info
                break
        
        if found_user:
            print("\n--- Hasil Pencarian ---")
            print(f"Username      : {found_user['username']}")
            print(f"Status        : {'✅ Following Back' if found_user['is_following_back'] else '❌ Not Following Back'}")
            print(f"Waktu Follow  : {found_user['followed_since']}")
            print("-" * 25)
        else:
            print(f"Username '{search_query}' tidak ditemukan dalam daftar following Anda.")
            
        print("\n")

if __name__ == "__main__":
    # --- Logo ASCII Art ---
    project_name = "Gramchekly"
    version = "v1.0"
    author = "Created by llkgunawann"

    print("\n" + "="*70)
    print(r"   _____                          _               _    _       ")
    print(r"  / ____|                        | |             | |  | |      ")
    print(r" | |  __ _ __ __ _ _ __ ___   ___| |__   ___  ___| | _| |_   _ ")
    print(r" | | |_ | '__/ _` | '_ ` _ \ / __| '_ \ / _ \/ __| |/ / | | | |")
    print(r" | |__| | | | (_| | | | | | | (__| | | |  __/ (__|   <| | |_| |")
    print(r"  \_____|_|  \__,_|_| |_| |_|\___|_| |_|\___|\___|_|\_\_|\__, |")
    print(r"                                                          __/ |")
    print(r"                                                         |___/ ")
    print(f"                                   {project_name} {version}")
    print(f"                                   {author}")
    print("="*70 + "\n")

    # --- Input Username tanpa validasi online ---
    # Perubahan di baris ini
    my_username = input("Masukan username : ").strip()
    if not my_username:
        print("Username tidak boleh kosong. Program dihentikan.")
        sys.exit()

    # --- Pilihan Aksi ---
    print("\nPilih opsi:")
    print("1. Install & Scan Data")
    print("2. Langsung eksekusi")
    
    user_choice = input("Pilihanmu (1/2): ").strip()
    
    followers_file = "./followers_1.json"
    following_file = "./following.json"
    
    report_data = None # Variabel untuk menyimpan data hasil laporan

    if user_choice == '1':
        print("\n--- Opsi 1: Install & Scan Data ---")
        check_dependencies()
        
        if os.path.exists(followers_file) and os.path.exists(following_file):
            print("Status file data: 📂 File ditemukan!")
            confirm = input("Lanjut pengecekan follow-back? (y/n): ").strip().lower()
            if confirm == 'y':
                report_data = run_check_and_report(my_username, followers_file, following_file)
            else:
                print("Pengecekan dibatalkan.")
        else:
            print("Status file data: ⚠️ File tidak ditemukan.")
            show_download_instructions()
            
    elif user_choice == '2':
        print("\n--- Opsi 2: Langsung eksekusi ---")
        if os.path.exists(followers_file) and os.path.exists(following_file):
            print("File ditemukan. Langsung mengecek...")
            report_data = run_check_and_report(my_username, followers_file, following_file)
        else:
            print("⚠️ File data tidak ditemukan. Mengalihkan ke opsi 1 untuk petunjuk download.")
            show_download_instructions()
            
    else:
        # Pastikan baris 'else:' ini memiliki titik dua
        print("Pilihan tidak valid. Program dihentikan.")
        
    # --- Panggil fitur pencarian jika laporan berhasil dibuat ---
    if report_data is not None:
        search_by_username_feature(report_data)

    sys.exit()