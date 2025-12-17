import os
import requests
import json

def openfold3_predict(
    molecules: list,
    msas: list = None,
    num_samples: int = 1,
    base_url: str = None
) -> dict:
    """
    Predict structure using OpenFold3 NIM.
    
    Args:
        molecules: List of dicts, e.g.:
            [
                {"type": "protein", "sequence": "MVSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTLTYGVQCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLVNRIELKGIDFKEDGNILGHKLEYNYNSHNVYIMADKQKNGIKVNFKIRHNIEDGSVQLADHYQQNTPIGDGPVLLPDNHYLSTQSALSKDPNEKRDHMVLLEFVTAAGITLGMDELYK"},
                {"type": "ligand", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}  # Aspirin
            ]
        msas: Optional pre-paired MSAs (advanced).
        num_samples: Number of diffusion samples (1-10 for diversity).
        base_url: Override endpoint (default uses hosted if key set, else local).
    
    Returns:
        Dict with PDB strings, confidence (pLDDT), etc.
    """
    api_key = os.getenv("NVIDIA_API_KEY")  # nvapi- key works for hosted BioNeMo

    if base_url is None:
        if api_key:
            base_url = "https://ai.api.nvidia.com/v1/biology/openfold/openfold3"
        else:
            base_url = "http://localhost:8000/biology/openfold/openfold3"

    url = f"{base_url}/predict"

    payload = {
        "molecules": molecules,
        "num_samples": num_samples,
    }
    if msas:
        payload["msas"] = msas

    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        result = response.json()
        
        # Extract key outputs
        pdb = result.get("structures", [{}])[0].get("pdb", "")
        confidence = result.get("confidence", {})
        
        return {
            "pdb_content": pdb,
            "plddt_avg": sum(confidence.get("plddt", [])) / len(confidence.get("plddt", [1])) if confidence.get("plddt") else 0,
            "full_result": result
        }
    except Exception as e:
        return {"error": str(e), "response": response.text if 'response' in locals() else ""}

# Example usage (test it!)
if __name__ == "__main__":
    result = openfold3_predict([
        {"type": "protein", "sequence": "MKFLVNVALVFMVVYISYIYA"},  # Small test peptide
        {"type": "ligand", "smiles": "CCO"}  # Ethanol
    ])
    print(json.dumps(result, indent=2))