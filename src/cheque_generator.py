from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color, black, white, gray
from reportlab.lib.utils import ImageReader
import os
import io
import requests
from PIL import Image, ImageOps

# Register fonts
pdfmetrics.registerFont(TTFont('MICR', os.path.join('assets', 'fonts', 'E13B.ttf')))
# Standard fonts are registered by default in reportlab

class ChequeGenerator:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        # Standard Letter size (8.5" x 11")
        self.width, self.height = letter

    def generate(self, data):
        """
        Generates a full page PDF (Remittance Advice + Cheque).
        """
        filename = os.path.join(self.output_dir, f"cheque_{data['cheque_number']}.pdf")
        c = canvas.Canvas(filename, pagesize=letter)
        
        # Draw Remittance Advice at the top
        self._draw_remittance_advice(c, data)
        
        # Draw Cheque at the bottom (Offset 0)
        self._draw_cheque(c, data, offset_y=0)
        
        c.save()
        print(f"Successfully generated: {filename}")
        return filename

    def _draw_remittance_advice(self, c, data):
        """Draws the top 2/3 of the page (Voucher/Remittance Advice)"""
        # --- FROM SECTION ---
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.0 * inch, 10.2 * inch, "FROM:")
        
        c.setFont("Helvetica", 9)
        c.drawString(1.5 * inch, 10.2 * inch, data.get('employer_name', '').split('\n')[0])
        c.setFont("Helvetica", 9)
        y = 10.08 * inch
        # Handle multi-line employer name properly
        name_lines = data.get('employer_name', '').split('\n')
        if len(name_lines) > 1:
            for line in name_lines[1:]:
                if line.strip():
                    c.drawString(1.5 * inch, y, line)
                    y -= 0.12 * inch
        
        c.drawString(1.5 * inch, y, data.get('employer_street', ''))
        y -= 0.12 * inch
        c.drawString(1.5 * inch, y, data.get('employer_city_state_zip', ''))

        # --- TO SECTION (Positioned for window envelopes) ---
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.0 * inch, 9.1 * inch, "TO:")
        
        c.setFont("Courier", 10)
        y = 9.1 * inch
        c.drawString(1.5 * inch, y, data.get('payee_name', ''))
        y -= 0.12 * inch
        for line in data.get('payee_address', '').split('\n'):
            if line.strip():
                c.drawString(1.5 * inch, y, line)
                y -= 0.12 * inch

        # --- REFERENCE INFO (Top Right) ---
        c.setFont("Courier", 9)
        ref_x = 7.8 * inch
        c.drawRightString(ref_x, 9.1 * inch, f" {data.get('date', '')}")
        c.drawRightString(ref_x, 8.95 * inch, f"CHECK NO. : {data.get('cheque_number', '')}")
        c.drawRightString(ref_x, 8.8 * inch, f" {data.get('voucher_id', '')}")
        # Masked SSN
        ssn = data.get('ssn', '')
        masked_ssn = "XXXXX" + ssn[-4:] if len(ssn) >= 4 else ssn
        c.drawRightString(ref_x, 8.65 * inch, f" {masked_ssn}")

        # --- SUMMARY DATA (Requested Plain Column Format) ---
        y_sum = 7.9 * inch
        c.setFont("Courier", 9)
        # Column headers (Horizontal spacing)
        c.drawCentredString(1.5 * inch, y_sum, "GROSS AMT")
        c.drawCentredString(3.5 * inch, y_sum, "FED. W/H")
        c.drawCentredString(5.5 * inch, y_sum, "H&W INS")
        c.drawCentredString(7.5 * inch, y_sum, "CHECK AMT")
        
        # Column values below headers
        y_val = y_sum - 0.25 * inch
        c.drawCentredString(1.5 * inch, y_val, data.get('gross_amt', ''))
        c.drawCentredString(3.5 * inch, y_val, data.get('fed_wh', ''))
        c.drawCentredString(5.5 * inch, y_val, data.get('hw_ins', ''))
        formatted_net = f"${data.get('amount', 0):,.2f}"
        c.drawCentredString(7.5 * inch, y_val, formatted_net)

        # --- MEMO & NOTICE ---
        c.setFont("Courier", 9.5)
        c.drawString(1.0 * inch, 6.8 * inch, f"MEMO: {data.get('memo', '')}")
        
        c.setFont("Courier", 10)
        notice_text = [
            "IN THE EVENT YOU DO NOT RECEIVE YOUR CHECK ON THE FIRST OF THE MONTH,",
            "DO NOT CONTACT THE FUND ADMINISTRATION OFFICE UNTIL AFTER THE TENTH",
            "(10TH) OF THE MONTH, SINCE NO STOP-PAYMENT ORDERS MAY BE PLACED ON",
            "LOST CHECKS UNTIL AFTER THE (10TH) TENTH OF THE MONTH IN WHICH THEY ARE",
            "ISSUED."
        ]
        y_notice = 6.4 * inch
        for line in notice_text:
            c.drawString(1.0 * inch, y_notice, line)
            y_notice -= 0.15 * inch

    def _draw_cheque(self, c, data, offset_y=0):
        """
        Draws the bank-standard cheque portion at a specific vertical offset.
        """
        # Adjust all coordinates by offset_y
        def oy(y): return y + offset_y
        
        # --- Layout Constants ---
        width = 8.5 * inch
        
        # --- VOID Background Watermark ---
        c.saveState()
        # Define clipping rectangle to keep watermark inside the frame borders only
        # Inner frame: width 8.1" starting at 0.2", height from 0.65" to 3.47" (approx 2.82" tall)
        clip_path = c.beginPath()
        clip_path.rect(0.2 * inch, oy(0.65 * inch), 8.1 * inch, 2.82 * inch)
        c.clipPath(clip_path, stroke=0, fill=0)
        
        c.setFont("Helvetica-Bold", 45)
        c.setFillAlpha(0.05) # Very subtle
        for i in range(0, 10, 2):
            for j in range(0, 5):
                # Skip watermark in the signature area (bottom right approximately)
                # x positions map to i, y positions map to j
                # signature is around x=5.7", y=0.9" relative to oy
                # if i >= 6 and j <= 1:
                #     continue
                    
                c.saveState()
                c.translate(i * 1.0 * inch, j * 0.8 * inch)
                c.rotate(1)
                c.drawCentredString(0, 0, "VOID")
                c.restoreState()
        c.restoreState()

        # --- Top and Bottom Bars (Precise Alignment) ---
        c.setFillColorRGB(0.2, 0.2, 0.2)
        # Top bar: thicker (2x)
        c.rect(0.2 * inch, oy(3.35 * inch), 8.1 * inch, 0.22 * inch, fill=1, stroke=0)
        # Bottom bar: thinner (1x)
        c.rect(0.2 * inch, oy(0.65 * inch), 8.1 * inch, 0.12 * inch, fill=1, stroke=0)
        
        # Side Borders (Very thin)
        c.setLineWidth(0.5) # Thin line
        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        # Left Line
        c.line(0.2 * inch, oy(0.65 * inch), 0.2 * inch, oy(3.47 * inch))
        # Right Line
        c.line(8.3 * inch, oy(0.65 * inch), 8.3 * inch, oy(3.47 * inch))
        c.setLineWidth(1) # Reset line width
        c.setFillColorRGB(0, 0, 0) # Reset to black
        c.setStrokeColorRGB(0, 0, 0)

        # Employer Info - Aligned at the same level as Cheque Number
        c.setFont("Helvetica-Bold", 10)
        y_emp = oy(3.15 * inch)
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
        table_x, table_y = 0.5 * inch, oy(2.4 * inch)
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
        y_bank = oy(2.15 * inch)
        for line in data['bank_info'].split('\n'):
            c.drawString(0.6 * inch, y_bank, line)
            y_bank -= 0.1 * inch

        # Amount Words
        c.setFont("Courier", 11)
        c.drawCentredString(width / 2, oy(1.7 * inch), data['amount_words'])

        # --- Amount Section (Centered Column) ---
        amount_center_x = 7.5 * inch
        
        # Cheque Number
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(amount_center_x, oy(3.15 * inch), data['cheque_number'])
        
        # 69-39/519 (Fractional number)
        # c.setFont("Helvetica", 9)
        # c.drawRightString(6.5 * inch, 3.0 * inch, "69-39/519")

        # Label: PAY THIS AMOUNT
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(amount_center_x, oy(2.85 * inch), "PAY THIS AMOUNT")
        
        # Amount Box
        box_w, box_h = 1.35 * inch, 0.45 * inch
        c.setLineWidth(1.0)
        c.rect(amount_center_x - box_w/2, oy(2.35 * inch), box_w, box_h)
        
        c.setFont("Courier-Bold", 13)
        formatted_amount = f"${data['amount']:,.2f}"
        c.drawCentredString(amount_center_x, oy(2.45 * inch), formatted_amount)
        
        # VOID AFTER 90 DAYS
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(amount_center_x, oy(2.2 * inch), "VOID AFTER 90 DAYS")

        # Payee Info with Bullets (Bold and relatively smaller)
        c.setFont("Helvetica-Bold", 7)
        labels = [("PAY TO", 1.35), ("THE ORDER", 1.15), ("OF", 0.95)]
        for label, y_pos in labels:
            c.drawString(0.7 * inch, y_pos * inch, label)
            c.drawCentredString(1.4 * inch, y_pos * inch, "*")
        
        c.setFont("Courier", 11)
        # payee name and address
        c.drawString(1.7 * inch, oy(1.3 * inch), data['payee_name'])
        y_payee_addr = oy(1.15 * inch)
        for line in data['payee_address'].split('\n'):
            c.drawString(1.7 * inch, y_payee_addr, line)
            y_payee_addr -= 0.15 * inch

        # Signature Line and MICR Line drawn first
        c.line(5.5 * inch, oy(0.85 * inch), 8.1 * inch, oy(0.85 * inch))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(5.5 * inch, oy(0.95 * inch), "") 

        # --- MICR Line (US Standard Pattern) ---
        c.setFont("MICR", 14)
        
        # --- MICR Line (US Standard Pattern - Letter Mapping) ---
        c.setFont("MICR", 14)
        
        # User verified pattern for E13B.ttf:
        # A = Transit, B = On-Us
        # Final Format: B{check}B A{routing}A {account}B{serial}B
        cheque_no = str(data.get('cheque_number', ''))
        routing_no = str(data.get('routing_number', data.get('transit_number', '')))
        account_no = str(data.get('account_number', ''))
        serial = str(data.get('micr_serial', ''))
        
        # Build the string using Letter Pattern A
        # micr_string = f'B{cheque_no}B A{routing_no}A {account_no}B{serial}B'
        micr_string = f'C{cheque_no}C A{routing_no}A {account_no}D{serial}C'
        
        # Print the constructed MICR line
        c.drawString(1.4 * inch, oy(0.4 * inch), micr_string)

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
                    
                    # PROCESS: Handle transparency for signature on white paper
                    img_raw = Image.open(io.BytesIO(response.content)).convert('RGBA')
                    
                    # 1. Convert to grayscale to identify lightness
                    gray = img_raw.convert('L')
                    
                    # 2. Invert to find the pen strokes (dark becomes light)
                    inverted = ImageOps.invert(gray)
                    
                    # 3. Use the inverted grayscale as the alpha mask
                    # This makes dark pen strokes more opaque and white paper transparent
                    # Boost contrast to ensure strokes are sharp and background is cleared
                    alpha_mask = inverted.point(lambda x: min(255, int(x * 2.4)))
                    
                    # 4. Apply the alpha mask directly to the original image
                    # This preserves original colors (ink color) while making the paper transparent
                    img_raw.putalpha(alpha_mask)
                    img_transparent = img_raw
                    
                    # 5. Robust Crop to the signature itself
                    bbox = alpha_mask.getbbox()
                    if bbox:
                        # Extra internal crop to remove edge artifacts (black pixels at corners)
                        edge_trim = 20
                        padding = 10
                        img_cropped = img_transparent.crop((
                            max(0, bbox[0] + edge_trim), 
                            max(0, bbox[1] + edge_trim), 
                            min(img_raw.width, bbox[2] - edge_trim), 
                            min(img_raw.height, bbox[3] - edge_trim)
                        ))
                    else:
                        img_cropped = img_transparent

                    # Resize to reasonable width if needed
                    if img_cropped.width > 1200:
                        img_cropped = img_cropped.resize((1200, int(img_cropped.height * (1200 / img_cropped.width))), Image.LANCZOS)
                    
                    # Store as ImageReader for direct rendering
                    # We keep it as RGBA to preserve transparency over the watermark
                    final_sig_data = ImageReader(img_cropped)
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
                    # c.drawImage(final_sig_data, 5.7 * inch, oy(0.9 * inch), width=2.5*inch, height=0.6*inch, preserveAspectRatio=True)
                    c.drawImage(final_sig_data, 5.6 * inch, oy(0.88 * inch),
                        width=2.9 * inch, height=0.8 * inch,
                        preserveAspectRatio=True,
                        mask='auto')
                    print(f"SUCCESS: Rendered signature for cheque {data.get('cheque_number', 'unknown')}")
                except Exception as e:
                    print(f"ERROR: Failed to draw image: {e}")

        # Removed standalone save/return as this is now a helper method
        return

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
