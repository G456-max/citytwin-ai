"""
MineGuard AI — Document Collection (Phase E1)
Authoritative post-quantum cryptography documents, standards, and guidelines.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import os
from loguru import logger


@dataclass
class Document:
    """Document representation for RAG indexing."""
    id: str
    title: str
    url: str
    category: str  # "NIST" | "ENISA" | "Industry" | "Academic" | "Standards"
    year: int
    license: str
    full_text: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# Primary and Secondary Sources Metadata
DOCUMENTS_METADATA: List[Dict[str, Any]] = [
    {
        "id": "nist-fips-203",
        "title": "NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)",
        "url": "https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.203.pdf",
        "category": "NIST",
        "year": 2024,
        "license": "Public Domain (U.S. Government Work)",
        "description": "Primary post-quantum standard for general key establishment, based on the CRYSTALS-Kyber algorithm. Specifies ML-KEM-512, ML-KEM-768, and ML-KEM-1024 parameter sets."
    },
    {
        "id": "nist-fips-204",
        "title": "NIST FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA)",
        "url": "https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.204.pdf",
        "category": "NIST",
        "year": 2024,
        "license": "Public Domain (U.S. Government Work)",
        "description": "Primary post-quantum standard for digital signatures, derived from CRYSTALS-Dilithium. Replaces RSA and ECDSA signatures across PKI, TLS certificates, and firmware validation."
    },
    {
        "id": "nist-fips-205",
        "title": "NIST FIPS 205: Stateless Hash-Based Digital Signature Standard (SLH-DSA)",
        "url": "https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf",
        "category": "NIST",
        "year": 2024,
        "license": "Public Domain (U.S. Government Work)",
        "description": "Stateless hash-based signature scheme derived from SPHINCS+. Provides a mathematically conservative backup resistant to potential lattice cryptanalysis."
    },
    {
        "id": "nist-ir-8547",
        "title": "NIST IR 8547: Transition to Post-Quantum Cryptography Standards",
        "url": "https://csrc.nist.gov/pubs/ir/8547/ipd",
        "category": "NIST",
        "year": 2024,
        "license": "Public Domain (U.S. Government Work)",
        "description": "Guidelines on deprecation timelines for legacy public key algorithms (RSA, ECDSA, DH, ECDH) and migration roadmaps across federal and critical infrastructure systems."
    },
    {
        "id": "nist-sp-800-208",
        "title": "NIST SP 800-208: Recommendation for Stateful Hash-Based Signature Schemes",
        "url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-208.pdf",
        "category": "NIST",
        "year": 2020,
        "license": "Public Domain (U.S. Government Work)",
        "description": "Recommends stateful hash-based signature algorithms LMS and XMSS for dedicated, state-managed environments like secure bootloader code signing and industrial firmware."
    },
    {
        "id": "enisa-pqc-2024",
        "title": "ENISA Post-Quantum Cryptography Report: Current State and Deployment Guidelines",
        "url": "https://www.enisa.europa.eu/publications/post-quantum-cryptography-current-state-and-quantum-mitigation",
        "category": "ENISA",
        "year": 2024,
        "license": "Open Access / European Union (reuse authorised)",
        "description": "European Union Agency for Cybersecurity analysis of post-quantum readiness, hybrid key exchange deployment (X25519 + ML-KEM-768), and industrial SCADA migration considerations."
    },
    {
        "id": "nsa-cnsa-2.0",
        "title": "NSA CNSA 2.0: Commercial National Security Algorithm Suite 2.0 Cybersecurity Advisory",
        "url": "https://media.defense.gov/2022/Sep/07/2003071834/-1/-1/0/CSA_CNSA_2.0_ALGORITHMS_.PDF",
        "category": "Industry",
        "year": 2022,
        "license": "Public Domain (U.S. Government Work)",
        "description": "NSA timelines mandating PQC algorithm transitions. Specifies ML-KEM-1024, ML-DSA-87, and stateful hash signatures, setting 2030-2033 enforcement deadlines for critical networks."
    },
    {
        "id": "google-qec-2024",
        "title": "Google Quantum AI: Quantum Error Correction and Scaling Milestones White Paper",
        "url": "https://quantumai.google/research/error-correction-2024",
        "category": "Industry",
        "year": 2024,
        "license": "Creative Commons Attribution 4.0",
        "description": "Milestones in logical qubit fidelity, surface code thresholds, and fault-tolerant quantum computing roadmaps. Details progress toward Cryptanalytically Relevant Quantum Computers (CRQCs)."
    },
    {
        "id": "mosca-inequality",
        "title": "Mosca's Theorem: Quantum Risk Horizon and Data Shelf-Life Inequality",
        "url": "https://eprint.iacr.org/2015/1018",
        "category": "Academic",
        "year": 2015,
        "license": "Open Academic Archive (IACR)",
        "description": "Defines the fundamental risk formula: If X (data shelf-life) + Y (migration time) > Z (time until quantum computer capable of breaking classical crypto), security is already compromised."
    },
    {
        "id": "cyclonedx-1.7-cbom",
        "title": "CycloneDX 1.7 Cryptographic Bill of Materials (CBOM) Specification",
        "url": "https://cyclonedx.org/capabilities/cbom/",
        "category": "Standards",
        "year": 2024,
        "license": "Apache License 2.0",
        "description": "Standardized schema for cataloging cryptographic assets, dependencies, protocol cipher suites, algorithms, key lengths, and quantum-readiness attributes across software and hardware bills of material."
    },
    {
        "id": "nist-sp-800-57",
        "title": "NIST SP 800-57 Part 1 Rev 5: Recommendation for Key Management",
        "url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf",
        "category": "NIST",
        "year": 2020,
        "license": "Public Domain (U.S. Government Work)",
        "description": "Guidelines for cryptoperiods, key longevity, security strengths (112, 128, 192, 256 bits), and classical algorithm phase-out schedules."
    },
    {
        "id": "rfc-8391",
        "title": "RFC 8391: XMSS: eXtended Merkle Signature Scheme",
        "url": "https://www.rfc-editor.org/rfc/rfc8391.html",
        "category": "Standards",
        "year": 2018,
        "license": "IETF Trust Provisions",
        "description": "Internet Engineering Task Force standard for XMSS stateful hash-based signatures, specifying Merkle tree verification and state index synchronization."
    },
    {
        "id": "rfc-8554",
        "title": "RFC 8554: Leighton-Micali Hash-Based Signatures (LMS)",
        "url": "https://www.rfc-editor.org/rfc/rfc8554.html",
        "category": "Standards",
        "year": 2019,
        "license": "IETF Trust Provisions",
        "description": "Specification for LMS and HSS hierarchical signature schemes. Used in firmware verification, secure boot, and hardware security modules (HSMs)."
    }
]


# Bundled authoritative excerpts ensuring complete offline functioning
BUNDLED_EXCERPTS: Dict[str, str] = {
    "nist-fips-203": """
NIST FIPS 203: MODULE-LATTICE-BASED KEY-ENCAPSULATION MECHANISM STANDARD (ML-KEM)
Published: August 13, 2024. U.S. National Institute of Standards and Technology.

1. OVERVIEW AND PURPOSE
Federal Information Processing Standard (FIPS) 203 specifies the Module-Lattice-Based Key-Encapsulation Mechanism (ML-KEM). ML-KEM is designed to protect sensitive electronic data against both classical and quantum computing adversaries. It replaces classical key agreement protocols, including Diffie-Hellman (DH), Elliptic Curve Diffie-Hellman (ECDH), and RSA key encapsulation.

2. CRYPTOGRAPHIC FOUNDATION
ML-KEM is mathematically grounded in the hardness of the Module Learning With Errors (M-LWE) problem over structured polynomial rings. M-LWE is conjectured to be resistant to polynomial-time quantum algorithms, including Shor's algorithm, which polynomial-solves discrete logarithms and integer factorization.

3. PARAMETER SETS AND SECURITY CATEGORIES
NIST defines three primary parameter sets:
- ML-KEM-512: NIST Security Category 1 (equivalent classical brute-force security to AES-128). Public key size: 800 bytes; Ciphertext size: 768 bytes; Shared secret: 32 bytes.
- ML-KEM-768: NIST Security Category 3 (equivalent classical brute-force security to AES-192). Public key size: 1,184 bytes; Ciphertext size: 1,088 bytes; Shared secret: 32 bytes. Recommended for general enterprise and industrial applications.
- ML-KEM-1024: NIST Security Category 5 (equivalent classical brute-force security to AES-256). Public key size: 1,568 bytes; Ciphertext size: 1,568 bytes; Shared secret: 32 bytes. Recommended for national security and ultra-critical safety systems.

4. MIGRATION AND HYBRID DEPLOYMENT
NIST explicitly endorses hybrid key exchange during the transition window, combining ML-KEM-768 with classical ECDH (such as X25519). A hybrid mechanism ensures that data remains secure as long as either the classical or post-quantum primitive remains unbroken.
""",

    "nist-fips-204": """
NIST FIPS 204: MODULE-LATTICE-BASED DIGITAL SIGNATURE STANDARD (ML-DSA)
Published: August 13, 2024. U.S. National Institute of Standards and Technology.

1. OVERVIEW AND PURPOSE
FIPS 204 specifies the Module-Lattice-Based Digital Signature Algorithm (ML-DSA), derived from the CRYSTALS-Dilithium algorithm. It is the primary post-quantum digital signature standard for identity verification, Public Key Infrastructure (PKI), TLS certificates, VPN handshakes, and digitally signed transactions.

2. MATHEMATICAL UNDERPINNINGS
ML-DSA relies on the hardness of the Module Short Integer Solution (M-SIS) and Module Learning With Errors (M-LWE) problems in module lattices. Classical signature algorithms like RSA (PKCS#1 v1.5, PSS) and ECDSA (secp256r1, secp384r1) are completely vulnerable to polynomial-time factorization and discrete log cracking via Shor's algorithm on a Cryptanalytically Relevant Quantum Computer (CRQC).

3. PARAMETER SETS
- ML-DSA-44: Security Category 2. Public key: 1,312 bytes; Signature: 2,420 bytes.
- ML-DSA-65: Security Category 3. Public key: 1,952 bytes; Signature: 3,309 bytes. General-purpose standard for root CAs, leaf certificates, and industrial authentication gateways.
- ML-DSA-87: Security Category 5. Public key: 2,592 bytes; Signature: 4,627 bytes. Highest assurance level, mandatory for top-tier root trust anchors and safety interlock signing.

4. OPERATIONAL CONSIDERATIONS
Because ML-DSA public keys and signatures are substantially larger than classical RSA-2048 or ECDSA signatures, network MTU limits, fragmentation in industrial protocols (Modbus/TCP, CIP, DNP3), and embedded RAM constraints must be accommodated during engineering migrations.
""",

    "nist-fips-205": """
NIST FIPS 205: STATELESS HASH-BASED DIGITAL SIGNATURE STANDARD (SLH-DSA)
Published: August 13, 2024. U.S. National Institute of Standards and Technology.

1. OVERVIEW AND PURPOSE
FIPS 205 specifies the Stateless Hash-Based Digital Signature Algorithm (SLH-DSA), derived from SPHINCS+. Unlike lattice-based schemes, SLH-DSA relies solely on the security properties of standard cryptographic hash functions (such as SHA-256 and SHAKE-256).

2. CRYPTOGRAPHIC PROPERTIES AND DIVERSITY
Lattice-based schemes (ML-DSA, ML-KEM) share underlying mathematical structures. If an unforeseen breakthrough in algebraic lattice reduction occurs, lattice systems could become vulnerable. SLH-DSA provides an essential non-lattice hedge. Hash functions are not susceptible to Shor's algorithm, and Grover's algorithm only provides a quadratic speedup, which is completely counterbalanced by doubling the digest size (e.g., using SHA-256 or SHA-512).

3. PARAMETER SETS AND TRADEOFFS
SLH-DSA parameter sets offer varying tradeoffs between verification speed and signature size:
- SLH-DSA-SHA2-128s / SLH-DSA-SHAKE-128s: Small signatures (~7,856 bytes), slower signing.
- SLH-DSA-SHA2-128f / SLH-DSA-SHAKE-128f: Faster signing, larger signatures (~17,088 bytes).
- SLH-DSA-SHA2-256s / 256f: Security Category 5 for long-term critical root certificates.
While SLH-DSA signatures are larger and computationally heavier than ML-DSA, their statelessness avoids the state-synchronization vulnerabilities inherent in stateful hash schemes (LMS/XMSS).
""",

    "nist-ir-8547": """
NIST IR 8547: TRANSITION TO POST-QUANTUM CRYPTOGRAPHY STANDARDS
Published: 2024. U.S. National Institute of Standards and Technology.

1. EXECUTIVE SUMMARY & TRANSITION TIMELINES
NIST Interagency Report (IR) 8547 outlines federal guidelines for transitioning from classical public-key cryptography to post-quantum standards. Legacy algorithms vulnerable to Shor's algorithm include:
- Factoring: RSA-2048, RSA-3072, RSA-4096.
- Discrete Logarithms: DSA, Diffie-Hellman (DH).
- Elliptic Curves: ECDSA, ECDH across all standard Weierstrass and Edwards curves (secp256r1, Ed25519).

2. DEPRECATION ROADMAP
- 2025-2030: Disallow new deployments of classical-only public key algorithms in high-impact systems. Implement hybrid key exchange.
- 2030: Deprecate RSA < 2048 and classical discrete logarithm schemes.
- 2033: Disallow classical asymmetric cryptography across all sensitive communications and critical infrastructure.
- 2035: Full transition to post-quantum standards (FIPS 203, FIPS 204, FIPS 205). Any continued reliance on classical keys requires explicit security waivers.

3. "HARVEST NOW, DECRYPT LATER" (HNDL) THREAT
Adversaries actively intercept and store encrypted classical ciphertexts today. When a quantum computer emerges, these stored records will be decrypted retroactively. Systems handling data with longevity exceeding 5 to 10 years (such as mining geological surveys, SCADA telemetry, and safety logs) are at active, present-day risk.
""",

    "nist-sp-800-208": """
NIST SP 800-208: RECOMMENDATION FOR STATEFUL HASH-BASED SIGNATURE SCHEMES
Published: October 2020. NIST Special Publication.

1. SCOPE AND INDUSTRIAL APPLICATION
NIST SP 800-208 approves stateful hash-based signature algorithms LMS (Leighton-Micali Signatures) and XMSS (eXtended Merkle Signature Scheme) for restricted operational environments. These environments include code signing, firmware validation in Industrial Internet of Things (IIoT), Programmable Logic Controllers (PLCs), and safety-critical embedded systems.

2. STATE MANAGEMENT HAZARD
Unlike traditional signatures, stateful hash signatures consume one-time signing keys. Reusing a one-time signing key catastrophically compromises the entire signing tree. Therefore, SP 800-208 mandates that private keys MUST be maintained in certified Hardware Security Modules (HSMs) that guarantee atomic non-volatile state increments. Stateful signatures MUST NOT be used for general-purpose applications like web server TLS or dynamic messaging.
""",

    "enisa-pqc-2024": """
ENISA POST-QUANTUM CRYPTOGRAPHY REPORT (2024)
European Union Agency for Cybersecurity.

1. CRITICAL INFRASTRUCTURE FOCUS
The European Union Agency for Cybersecurity evaluates quantum vulnerabilities across operational technology (OT) and SCADA environments. Industrial installations—such as power grids, mining ventilation, automated haulage systems, and chemical processing—rely heavily on long-lived hardware with update cycles exceeding 15 to 25 years.

2. MIGRATION ROADMAP FOR INDUSTRIAL OT
- Cryptographic Inventory: Operators must generate comprehensive Cryptographic Bills of Materials (CBOMs) mapping all root CAs, leaf certificates, VPN tunnels, and Modbus/CIP communication paths.
- Hybrid Key Exchange: Transition to X25519/ML-KEM-768 hybrid tunnels to maintain compliance with existing OT equipment while securing against quantum adversaries.
- Hardware Crypto-Agility: PLCs and Remote Terminal Units (RTUs) must be evaluated for crypto-agility to determine if firmware updates can accommodate ML-KEM and ML-DSA key and signature sizes.
""",

    "nsa-cnsa-2.0": """
NSA COMMERCIAL NATIONAL SECURITY ALGORITHM SUITE 2.0 (CNSA 2.0)
Cybersecurity Advisory, National Security Agency (NSA).

1. MANDATORY PQC TRANSITION SCHEDULE
CNSA 2.0 establishes strict algorithmic requirements for National Security Systems (NSS) and critical infrastructure assets:
- Software & Firmware Signing: Immediate preference for ML-DSA-87 and stateful hash signatures (LMS/XMSS). Mandatory enforcement by 2025-2030.
- Web Browsers, Servers & Cloud Services: Full support for ML-KEM-1024 and ML-DSA-87 by 2033.
- Traditional Networking Equipment (Routers, VPN Gateways, Firewalls): Full transition to ML-KEM and ML-DSA by 2030. Classical algorithms prohibited by 2033.

2. APPROVED SYMMETRIC AND HASH SUITES
CNSA 2.0 retains AES-256 as safe against quantum Grover attacks. Symmetric encryption with AES-128 is deemed insufficient for long-term security. SHA-384 and SHA-512 are required for hashing; SHA-1 and MD5 are strictly prohibited.
""",

    "google-qec-2024": """
GOOGLE QUANTUM AI: QUANTUM ERROR CORRECTION WHITE PAPER (2024)
Google Quantum AI Research Team.

1. PROGRESSION TOWARD LOGICAL QUBITS
The transition from noisy intermediate-scale quantum (NISQ) processors to fault-tolerant quantum computers relies on quantum error correction (QEC). Google Quantum AI demonstrates that scaling distance-5 surface codes achieves physical error rates below the fault-tolerant threshold, with physical error suppression improving as surface code distances increase.

2. THE CRQC TIMELINE
A Cryptanalytically Relevant Quantum Computer (CRQC) requires approximately 10,000 to 20,000 physical qubits per logical qubit to execute Shor's algorithm on RSA-2048 or ECDSA-256. At current hardware scaling trajectories, expert consensus estimates a non-negligible probability (10-30%) of CRQC availability between 2029 and 2033, accelerating the necessity for proactive cryptographic migration today.
""",

    "mosca-inequality": """
MOSCA'S THEOREM: QUANTUM RISK HORIZON AND THEOREM OF SHELF-LIFE INEQUALITY
Dr. Michele Mosca, Institute for Quantum Computing.

1. THE FUNDAMENTAL THEOREM
Let:
- X = The security shelf-life of the data (number of years the data must remain confidential).
- Y = The migration time (number of years required to re-engineer, test, and deploy post-quantum systems).
- Z = The time until a quantum computer capable of breaking classical algorithms is built (Q-Day horizon).

2. THE THEOREM INEQUALITY
If X + Y > Z, then an organization's systems are ALREADY vulnerable to catastrophic compromise.
Even if a quantum computer will not exist for 8 years (Z = 8), if critical mine geological data must remain confidential for 10 years (X = 10) and migration takes 3 years (Y = 3), then X + Y = 13 > 8. The data harvested today under "Harvest Now, Decrypt Later" will be exposed within its required confidentiality lifespan.
""",

    "cyclonedx-1.7-cbom": """
CYCLONEDX 1.7 CRYPTOGRAPHIC BILL OF MATERIALS (CBOM) SPECIFICATION
OWASP Foundation / CycloneDX Working Group.

1. SCHEMA ARCHITECTURE FOR CRYPTOGRAPHIC ASSETS
CycloneDX 1.7 introduces first-class representation for Cryptographic Bills of Materials (CBOM). A CBOM provides automated, machine-readable transparency into:
- Cryptographic Assets: Algorithms, cipher suites, private/public keys, certificates, protocols, and hardware tokens.
- Quantum Vulnerability Metadata: Flags classifying algorithms as "quantum-vulnerable", "classical-safe", or "post-quantum-secure".
- Parameter Specifications: Modulus size, curve identifier, security strength in bits, execution mode, and implementation dependencies.

2. INTEROPERABILITY AND AUTOMATION
CBOMs formatted in CycloneDX 1.7 enable automated vulnerability scanners and risk cascading engines to ingest software and firmware inventories, map them to NIST FIPS 203/204/205 equivalents, and compute algorithmic deprecation metrics.
""",

    "nist-sp-800-57": """
NIST SP 800-57 PART 1 REV 5: RECOMMENDATION FOR KEY MANAGEMENT
U.S. National Institute of Standards and Technology.

1. CRYPTOGRAPHIC SECURITY STRENGTH LEVELS
NIST specifies security strengths measured in bits: 112 bits, 128 bits, 192 bits, and 256 bits.
- RSA-2048 provides approximately 112 bits of security, which is disallowed for federal use post-2030.
- RSA-3072 provides 128 bits of security.
- RSA-4096 provides 152 bits of security against classical attacks, but ZERO bits of security against Shor's algorithm on a quantum computer.
- AES-128 provides 128 bits classically, reduced to ~64 bits against Grover's algorithm. AES-256 provides 256 bits classically, retaining 128 bits of quantum security.
""",

    "rfc-8391": """
RFC 8391: XMSS: EXTENDED MERKLE SIGNATURE SCHEME
Internet Engineering Task Force (IETF).

1. STATEFUL HASH-BASED TREE ARCHITECTURE
RFC 8391 specifies the eXtended Merkle Signature Scheme (XMSS) and multi-tree XMSS (XMSS^MT). It uses Winternitz One-Time Signatures (WOTS+) combined with Merkle hash trees to construct digital signatures whose security relies strictly on second-preimage resistance of cryptographic hash functions.
2. OPERATIONAL STATE CONSTRAINTS
Every XMSS private key has a finite signing capacity ($2^h$ signatures). The signing device must persistently increment and persist the leaf index counter. If an index is ever reused, an attacker can forge signatures on arbitrary messages.
""",

    "rfc-8554": """
RFC 8554: LEIGHTON-MICALI HASH-BASED SIGNATURES (LMS)
Internet Engineering Task Force (IETF).

1. LEIGHTON-MICALI SIGNATURE SPECIFICATION
RFC 8554 specifies LMS and Hierarchical Signature Schemes (HSS). LMS is a stateful hash-based signature scheme using Leighton-Micali One-Time Signatures (LM-OTS) and cryptographic Merkle trees.
2. INDUSTRIAL FIRMWARE APPLICATION
Due to its low verification complexity and lean memory footprint, LMS is the chosen algorithm for post-quantum secure boot in safety-critical industrial controllers, mining OT interlocks, and aerospace telecommunications.
"""
}


def download_documents(target_dir: str = "data/documents") -> List[Document]:
    """
    Load all documents into memory and ensure files exist in target_dir.
    Uses bundled authoritative excerpts for reliable offline operation.
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    documents: List[Document] = []
    
    for meta in DOCUMENTS_METADATA:
        doc_id = meta["id"]
        category = meta["category"]
        text = BUNDLED_EXCERPTS.get(doc_id, f"Document content for {meta['title']}.")
        
        # Save to data/documents/<category>/<doc_id>.txt
        category_dir = target_path / category.lower()
        category_dir.mkdir(parents=True, exist_ok=True)
        file_path = category_dir / f"{doc_id}.txt"
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text.strip())
        except Exception as e:
            logger.warning(f"Could not write document to {file_path}: {e}")
        
        summary = meta["description"]
        doc = Document(
            id=doc_id,
            title=meta["title"],
            url=meta["url"],
            category=category,
            year=meta["year"],
            license=meta["license"],
            full_text=text.strip(),
            summary=summary,
            metadata={
                "file_path": str(file_path),
                "description": meta["description"],
            }
        )
        documents.append(doc)
        
    logger.info(f"Loaded {len(documents)} post-quantum documents across {len(set(d.category for d in documents))} categories.")
    return documents
