import qrcode
from PIL import Image
from pathlib import Path

def genera_qrcode_messaggeria(testo, tipo="whatsapp", numero_telefono=None,
                              output_path="qrcode.png", logo_path=None,
                              logo_size_ratio=0.3):
    """
    Genera un QR code per diversi servizi di messaggistica con logo opzionale al centro.

    Parametri:
    - testo: Il messaggio da inviare
    - tipo: 'whatsapp', 'telegram', 'web' (link generico)
    - numero_telefono: Numero con prefisso internazionale (es. '393401234567' per WhatsApp)
    - output_path: Percorso dove salvare l'immagine
    - logo_path: Percorso del logo da inserire al centro (opzionale)
    - logo_size_ratio: Dimensione del logo rispetto al QR (default 0.3 = 30%)
    """

    # Costruisce l'URL in base al tipo
    if tipo.lower() == "whatsapp":
        if not numero_telefono:
            raise ValueError("Per WhatsApp serve il numero di telefono (es. '393401234567')")
        numero = ''.join(filter(str.isdigit, numero_telefono))
        url = f"https://wa.me/{numero}?text={testo}"

    elif tipo.lower() == "telegram":
        if numero_telefono:
            numero = ''.join(filter(str.isdigit, numero_telefono))
            url = f"https://t.me/+{numero}"
        else:
            url = testo

    elif tipo.lower() == "web":
        url = testo

    else:
        raise ValueError("Tipo non supportato. Usa: 'whatsapp', 'telegram', 'web'")

    # Crea il QR code con correzione errori alta (necessaria per il logo)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta correzione per il logo
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Genera l'immagine base
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # Se c'è un logo, lo aggiungiamo al centro
    if logo_path and Path(logo_path).exists():
        logo = Image.open(logo_path)

        # Calcola le dimensioni del logo
        qr_width, qr_height = img.size
        logo_max_size = int(min(qr_width, qr_height) * logo_size_ratio)

        # Ridimensiona il logo mantenendo le proporzioni
        logo.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)

        # Crea un bordo bianco intorno al logo per migliorare la leggibilità
        border_size = 10
        logo_with_border = Image.new('RGB',
                                     (logo.size[0] + border_size * 2,
                                      logo.size[1] + border_size * 2),
                                     'white')

        # Incolla il logo al centro del bordo bianco
        logo_with_border.paste(logo, (border_size, border_size),
                               logo if logo.mode == 'RGBA' else None)

        # Calcola la posizione centrale per il logo
        logo_pos = ((qr_width - logo_with_border.size[0]) // 2,
                    (qr_height - logo_with_border.size[1]) // 2)

        # Incolla il logo sul QR code
        img.paste(logo_with_border, logo_pos)

        print(f"✓ Logo aggiunto da: {logo_path}")

    # Salva l'immagine finale
    img.save(output_path, quality=95)
    print(f"✓ QR code salvato in: {output_path}")
    print(f"✓ URL codificato: {url}")

    return output_path


def genera_qrcode_personalizzato(url, output_path="qrcode.png", logo_path=None,
                                 colore_qr="black", colore_sfondo="white",
                                 logo_size_ratio=0.3):
    """
    Versione semplificata per creare QR code personalizzati con colori custom.

    Parametri:
    - url: L'URL o testo da codificare
    - output_path: Dove salvare il file
    - logo_path: Percorso del logo (opzionale)
    - colore_qr: Colore del QR code (es. "black", "#000000", "blue")
    - colore_sfondo: Colore dello sfondo (es. "white", "#FFFFFF")
    - logo_size_ratio: Dimensione del logo (0.1-0.4 consigliato)
    """

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=colore_qr, back_color=colore_sfondo).convert('RGB')

    # Aggiungi logo se specificato
    if logo_path and Path(logo_path).exists():
        logo = Image.open(logo_path)
        qr_width, qr_height = img.size
        logo_max_size = int(min(qr_width, qr_height) * logo_size_ratio)

        logo.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)

        # Bordo bianco
        border_size = 10
        logo_with_border = Image.new('RGB',
                                     (logo.size[0] + border_size * 2,
                                      logo.size[1] + border_size * 2),
                                     colore_sfondo)

        logo_with_border.paste(logo, (border_size, border_size),
                               logo if logo.mode == 'RGBA' else None)

        logo_pos = ((qr_width - logo_with_border.size[0]) // 2,
                    (qr_height - logo_with_border.size[1]) // 2)

        img.paste(logo_with_border, logo_pos)

    img.save(output_path, quality=95)
    print(f"✓ QR code personalizzato salvato in: {output_path}")

    return output_path


# === ESEMPI DI UTILIZZO ===

if __name__ == "__main__":

    # 1. WhatsApp con logo
    genera_qrcode_messaggeria(
        testo="Ciao, contattami per il progetto archeologico!",
        tipo="whatsapp",
        numero_telefono="393401234567",
        output_path="qr_whatsapp_logo.png",
        logo_path="logo_cnr.png",  # Sostituisci con il tuo logo
        logo_size_ratio=0.25
    )

    # 2. Telegram con logo
    genera_qrcode_messaggeria(
        testo="https://t.me/pyarchinit",
        tipo="telegram",
        output_path="qr_telegram_logo.png",
        logo_path="logo_pyarchinit.png"
    )

    # 3. Link web generico con logo e colori personalizzati
    genera_qrcode_personalizzato(
        url="https://github.com/pyarchinit/pyarchinit",
        output_path="qr_github_custom.png",
        logo_path="logo.png",
        colore_qr="#2C3E50",  # Blu scuro
        colore_sfondo="#ECF0F1",  # Grigio chiaro
        logo_size_ratio=0.3
    )

    # 4. QR code senza logo (funziona comunque)
    genera_qrcode_messaggeria(
        testo="https://www.ispc.cnr.it",
        tipo="web",
        output_path="qr_semplice.png"
    )

    print("\n✅ Tutti i QR code sono stati generati!")