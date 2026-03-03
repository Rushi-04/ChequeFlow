from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import landscape
from reportlab.lib.utils import ImageReader
import os
import io
import requests
from PIL import Image

# Register fonts
pdfmetrics.registerFont(TTFont('MICR', os.path.join('assets', 'fonts', 'E13B.ttf')))
# Standard fonts are registered by default in reportlab

class ChequeGenerator:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate(self, data):
        """
        Generates a single cheque PDF based on the provided data dictionary.
        data keys: employer_name, employer_address, date, ssn, bank_info,
                   payee_name, payee_address, amount, amount_words,
                   cheque_number, transit_number, account_number, micr_line, signature_path
        """
        filename = os.path.join(self.output_dir, f"cheque_{data['cheque_number']}.pdf")
        # Increase height from 3.5 to 3.7 to add top padding
        c = canvas.Canvas(filename, pagesize=(8.5 * inch, 3.7 * inch))
        
        # --- Layout Constants ---
        width, height = 8.5 * inch, 3.7 * inch
        
        # --- VOID Background Watermark ---
        c.saveState()
        # Define clipping rectangle to keep watermark inside the frame borders only
        # Inner frame: width 8.1" starting at 0.2", height from 0.65" to 3.47" (approx 2.82" tall)
        clip_path = c.beginPath()
        clip_path.rect(0.2 * inch, 0.65 * inch, 8.1 * inch, 2.82 * inch)
        c.clipPath(clip_path, stroke=0, fill=0)
        
        c.setFont("Helvetica-Bold", 45)
        c.setFillAlpha(0.05) # Very subtle
        for i in range(0, 10, 2):
            for j in range(0, 5):
                c.saveState()
                c.translate(i * 1.0 * inch, j * 0.8 * inch)
                c.rotate(1)
                c.drawCentredString(0, 0, "VOID")
                c.restoreState()
        c.restoreState()

        # --- Top and Bottom Bars (Precise Alignment) ---
        c.setFillColorRGB(0.2, 0.2, 0.2)
        # Top bar: thicker (2x)
        c.rect(0.2 * inch, 3.35 * inch, 8.1 * inch, 0.22 * inch, fill=1, stroke=0)
        # Bottom bar: thinner (1x)
        c.rect(0.2 * inch, 0.65 * inch, 8.1 * inch, 0.12 * inch, fill=1, stroke=0)
        
        # Side Borders (Very thin)
        c.setLineWidth(0.5) # Thin line
        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        # Left Line
        c.line(0.2 * inch, 0.65 * inch, 0.2 * inch, 3.47 * inch)
        # Right Line
        c.line(8.3 * inch, 0.65 * inch, 8.3 * inch, 3.47 * inch)
        c.setLineWidth(1) # Reset line width
        c.setFillColorRGB(0, 0, 0) # Reset to black
        c.setStrokeColorRGB(0, 0, 0)

        # Employer Info - Aligned at the same level as Cheque Number
        c.setFont("Helvetica-Bold", 10)
        y_emp = 3.15 * inch
        # Handle multi-line employer name properly
        for line in data['employer_name'].split('\n'):
            if line:
                c.drawString(0.5 * inch, y_emp, line)
                y_emp -= 0.12 * inch

        # Employer address (if any) starts after the name
        c.setFont("Helvetica", 8)
        y_addr = y_emp - 0.05 * inch
        for line in data['employer_address'].split('\n'):
            if line:
                c.drawString(0.5 * inch, y_addr, line)
                y_addr -= 0.12 * inch

        # --- Date & SSN Table (Refined) ---
        table_x, table_y = 0.5 * inch, 2.4 * inch
        table_w, table_h = 4.5 * inch, 0.5 * inch
        col1_w = 2.0 * inch
        header_h = 0.15 * inch

        # Main border
        c.setLineWidth(0.8)
        c.rect(table_x, table_y, table_w, table_h)
        # Header separator
        c.line(table_x, table_y + table_h - header_h, table_x + table_w, table_y + table_h - header_h)
        # Column separator
        c.line(table_x + col1_w, table_y, table_x + col1_w, table_y + table_h)
        
        c.setFont("Helvetica-Bold", 7)
        c.drawString(table_x + 0.05 * inch, table_y + table_h - header_h + 0.03 * inch, "DATE")
        c.drawString(table_x + col1_w + 0.05 * inch, table_y + table_h - header_h + 0.03 * inch, "SOCIAL SECURITY NUMBER")
        
        c.setFont("Courier-Bold", 12)
        # Aligned from the start (left) as requested
        c.drawString(table_x + 0.15 * inch, table_y + 0.08 * inch, data['date'])
        c.drawString(table_x + col1_w + 0.15 * inch, table_y + 0.08 * inch, data['ssn'])

        # Bank Info (Relatively smaller than information)
        c.setFont("Helvetica", 6.5) # Smaller as requested
        y_bank = 2.15 * inch
        for line in data['bank_info'].split('\n'):
            c.drawString(0.6 * inch, y_bank, line)
            y_bank -= 0.1 * inch

        # Amount Words
        c.setFont("Courier", 11)
        c.drawCentredString(width / 2, 1.7 * inch, data['amount_words'])

        # --- Amount Section (Centered Column) ---
        amount_center_x = 7.5 * inch
        
        # Cheque Number
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(amount_center_x, 3.15 * inch, data['cheque_number'])
        
        # 69-39/519 (Fractional number)
        # c.setFont("Helvetica", 9)
        # c.drawRightString(6.5 * inch, 3.0 * inch, "69-39/519")

        # Label: PAY THIS AMOUNT
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(amount_center_x, 2.85 * inch, "PAY THIS AMOUNT")
        
        # Amount Box
        box_w, box_h = 1.35 * inch, 0.45 * inch
        c.setLineWidth(1.0)
        c.rect(amount_center_x - box_w/2, 2.35 * inch, box_w, box_h)
        
        c.setFont("Courier-Bold", 13)
        formatted_amount = f"${data['amount']:,.2f}"
        c.drawCentredString(amount_center_x, 2.45 * inch, formatted_amount)
        
        # VOID AFTER 90 DAYS
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(amount_center_x, 2.2 * inch, "VOID AFTER 90 DAYS")

        # Payee Info with Bullets (Bold and relatively smaller)
        c.setFont("Helvetica-Bold", 7)
        labels = [("PAY TO", 1.35), ("THE ORDER", 1.15), ("OF", 0.95)]
        for label, y_pos in labels:
            c.drawString(0.7 * inch, y_pos * inch, label)
            c.drawCentredString(1.4 * inch, y_pos * inch, "*")
        
        c.setFont("Courier", 11)
        # payee name and address
        c.drawString(1.7 * inch, 1.3 * inch, data['payee_name'])
        y_payee_addr = 1.15 * inch
        for line in data['payee_address'].split('\n'):
            c.drawString(1.7 * inch, y_payee_addr, line)
            y_payee_addr -= 0.15 * inch

        # Signature Line and MICR Line drawn first
        c.line(5.5 * inch, 0.85 * inch, 8.1 * inch, 0.85 * inch)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(5.5 * inch, 0.95 * inch, "") 

        # MICR Line (From Database)
        c.setFont("MICR", 13)
        # The MICR line format: o<check>o t<transit>t <account>
        # Note: 'o' and 't' are often used as shorthand for specific MICR characters in some fonts
        # We will use the provided micr_line from data if it looks correct, 
        # but let's construct it to be safe.
        # Actually, let's use the symbols: t = transit, o = on-us, m = dash, c = amount
        # Looking at the image, it looks like: [Check #] [Transit] [Account]
        # micr_string = f"o{data['cheque_number']}o t{data['transit_number']}t {data['account_number']}"
        # c.drawString(1.2 * inch, 0.4 * inch, micr_string)
        
        # Using the direct micr_line from database as requested
        micr_string = data.get('micr_line', f"o{data['cheque_number']}o t{data['transit_number']}t {data['account_number']}")
        c.drawString(1.4 * inch, 0.4 * inch, micr_string)

        # --- DRAW SIGNATURE AT THE VERY END (For Visibility) ---
        sig_path = data.get('signature_path', '')
        if sig_path:
            final_sig_path = None
            
            # 1. Handle Remote URL (Google Drive etc.)
            if sig_path.startswith(('http://', 'https://')):
                try:
                    # Normalize Google Drive link to direct download
                    if 'drive.google.com' in sig_path:
                        if 'file/d/' in sig_path:
                            file_id = sig_path.split('file/d/')[1].split('/')[0]
                            sig_path = f'https://drive.google.com/uc?export=download&id={file_id}'
                        elif 'id=' in sig_path:
                            file_id = sig_path.split('id=')[1].split('&')[0]
                            sig_path = f'https://drive.google.com/uc?export=download&id={file_id}'
                    
                    response = requests.get(sig_path, timeout=10)
                    response.raise_for_status()
                    
                    # PROCESS
                    img_raw = Image.open(io.BytesIO(response.content)).convert('RGBA')
                    
                    # Robust Crop
                    from PIL import ImageOps
                    bbox = img_raw.getbbox()
                    if not bbox or (bbox[2]-bbox[0] > img_raw.width*0.9 and bbox[3]-bbox[1] > img_raw.height*0.9):
                        gray = img_raw.convert('L')
                        inverted = ImageOps.invert(gray)
                        bbox = inverted.getbbox()
                    
                    if bbox:
                        padding = 10
                        img_cropped = img_raw.crop((
                            max(0, bbox[0] - padding), 
                            max(0, bbox[1] - padding), 
                            min(img_raw.width, bbox[2] + padding), 
                            min(img_raw.height, bbox[3] + padding)
                        ))
                    else:
                        img_cropped = img_raw

                    # Resize to 1200px width
                    if img_cropped.width > 1200:
                        img_cropped = img_cropped.resize((1200, int(img_cropped.height * (1200 / img_cropped.width))), Image.LANCZOS)

                    # Flatten onto WHITE background
                    bg = Image.new('RGB', img_cropped.size, (255, 255, 255))
                    bg.paste(img_cropped, (0, 0), img_cropped if img_cropped.mode == 'RGBA' else None)
                    
                    # Store as ImageReader for direct rendering
                    # This avoids all file path/viewer caching issues
                    final_sig_data = ImageReader(bg)
                except Exception as e:
                    print(f"ERROR: Failed remote processing: {e}")
            
            # 2. Handle Local File Path
            else:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                abs_path = os.path.join(project_root, sig_path)
                path_to_use = abs_path if os.path.exists(abs_path) else sig_path
                if os.path.exists(path_to_use):
                    try:
                        final_sig_data = ImageReader(path_to_use)
                    except Exception as e:
                        print(f"ERROR: Local signature load failed: {e}")
            
            # 3. Draw the Signature
            if final_sig_data:
                try:
                    # Draw actual signature - Using parameters that proved successful in diagnostic mode
                    # x=5.7*inch puts it nicely in the signature area
                    c.drawImage(final_sig_data, 5.7 * inch, 0.9 * inch, width=2.5*inch, height=0.6*inch, preserveAspectRatio=True)
                    print(f"SUCCESS: Rendered signature for cheque {data.get('cheque_number', 'unknown')}")
                except Exception as e:
                    print(f"ERROR: Failed to draw image: {e}")

        c.save()
        return filename

if __name__ == "__main__":
    # Test generation
    gen = ChequeGenerator()
    test_data = {
        "employer_name": "EMPLOYER - TEAMSTERS LOCAL NOS. 175 & 505 PENSION TRUST FUND",
        "employer_address": "",
        "date": "1/28/25",
        "ssn": "XXX-XX-8626",
        "bank_info": "UNITED BANK\nCHARLESTON, WEST VIRGINIA",
        "payee_name": "CARRIE LARCH",
        "payee_address": "5907 MELWOOD DR\nCHARLESTON, WV 25313",
        "amount": 5949.00,
        "amount_words": "*** Five Thousand Nine Hundred Forty Nine Dollars And 00/100***",
        "cheque_number": "01389587",
        "transit_number": "051900395",
        "account_number": "043370452",
        "signature_path": "assets/signatures/sample_sig.png"
    }
    gen.generate(test_data)
    print("Sample cheque generated in outputs folder.")
