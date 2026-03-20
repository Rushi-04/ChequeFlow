import os
from cheque_generator import ChequeGenerator

class ChequeService:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.generator = ChequeGenerator(output_dir=self.output_dir)

    def get_or_generate_path(self, data, signature_id=None, signature_path=None):
        """
        Returns the absolute path to the cheque PDF variant.
        Generates it if it doesn't already exist.
        
        signature_id: If provided, generates/fetches the variant for this signature.
        signature_path: The physical path to the signature image to use.
        """
        cheque_no = data.get('cheque_number')
        
        if signature_id:
            filename = f"cheque_{cheque_no}_sig_{signature_id}.pdf"
            # Override for the generator
            render_data = data.copy()
            render_data['signature_path'] = signature_path
        else:
            filename = f"cheque_{cheque_no}_unsigned.pdf"
            render_data = data.copy()
            render_data['signature_path'] = None # Ensure unsigned

        target_path = os.path.join(self.output_dir, filename)
        
        # Variants: if file is not there, create it
        if not os.path.exists(target_path):
            print(f"Generating PDF variant for cheque {cheque_no} ({filename}) on demand...")
            # We must pass the filename to the generator or it will use its default
            # Actually, generator.generate returns the path it created. 
            # Let's ensure generator doesn't overwrite.
            # Generator currently uses data['cheque_number'] to build filename.
            # I should either update generator or handle it here.
            
            # Temporary hack to generator's logic: generator uses output_dir + cheque_number
            # Let's update generator to accept an optional custom filename.
            # Or just let generator do its thing and we rename it? Better update generator.
            
            target_path = self.generator.generate_variant(render_data, filename)
            
        return target_path

    def generate_batch(self, cheque_data_list):
        """Legacy support"""
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
