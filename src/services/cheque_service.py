import os
from cheque_generator import ChequeGenerator

class ChequeService:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.generator = ChequeGenerator(output_dir=self.output_dir)

    def get_or_generate_path(self, data):
        """
        Returns the absolute path to the cheque PDF.
        Generates it if it doesn't already exist.
        """
        cheque_no = data.get('cheque_number')
        filename = f"cheque_{cheque_no}.pdf"
        target_path = os.path.join(self.output_dir, filename)
        
        # On-demand generation: if file is not there, create it
        if not os.path.exists(target_path):
            print(f"Generating PDF for cheque {cheque_no} on demand...")
            target_path = self.generator.generate(data)
            
        return target_path

    def generate_batch(self, cheque_data_list):
        """Legacy batch support, now uses get_or_generate_path internally"""
        results = []
        for data in cheque_data_list:
            try:
                path = self.get_or_generate_path(data)
                results.append({
                    "id": data.get('id'),
                    "cheque_number": data.get('cheque_number'),
                    "success": True,
                    "pdf_path": path,
                    "filename": os.path.basename(path)
                })
            except Exception as e:
                results.append({
                    "id": data.get('id'),
                    "cheque_number": data.get('cheque_number'),
                    "success": False,
                    "error": str(e)
                })
        return results
