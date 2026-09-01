import fitz
import os

svg_code = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2200 1350" width="2200" height="1350" style="background-color: #ffffff; font-family: 'Arial', 'Helvetica Neue', sans-serif;">
  <defs>
    <!-- UML Markers -->
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#000000" />
    </marker>
    <style>
      .title-main { font-size: 26px; font-weight: bold; fill: #000000; text-anchor: middle; letter-spacing: 0.5px; }
      .title-sub { font-size: 15px; fill: #444444; text-anchor: middle; }
      .boundary-title { font-size: 20px; font-weight: bold; fill: #000000; }
      .package-title { font-size: 14px; font-weight: bold; fill: #222222; font-style: italic; }
      .actor-label { font-size: 16px; font-weight: bold; fill: #000000; text-anchor: middle; }
      .actor-sub { font-size: 12.5px; fill: #555555; text-anchor: middle; font-style: italic; }
      .usecase-text { font-size: 13.5px; font-weight: 600; fill: #000000; text-anchor: middle; }
      .usecase-sub { font-size: 11.5px; fill: #444444; text-anchor: middle; }
      .rel-text { font-size: 12px; font-weight: bold; fill: #000000; text-anchor: middle; background-color: #ffffff; }
      .condition-text { font-size: 11px; fill: #333333; text-anchor: middle; font-style: italic; }
      
      .uc-oval { fill: #ffffff; stroke: #000000; stroke-width: 1.8; }
      .uc-auto { fill: #ffffff; stroke: #000000; stroke-width: 1.8; stroke-dasharray: 4,3; }
      .assoc-line { stroke: #000000; stroke-width: 1.6; fill: none; }
      .dep-line { stroke: #000000; stroke-width: 1.5; stroke-dasharray: 6,4; fill: none; marker-end: url(#arrowhead); }
      .group-box { fill: #fafafa; stroke: #888888; stroke-width: 1.2; stroke-dasharray: 4,4; rx: 10; }
      .legend-box { fill: #ffffff; stroke: #666666; stroke-width: 1.2; rx: 6; }
    </style>
  </defs>

  <!-- Canvas Background -->
  <rect width="2200" height="1350" fill="#ffffff" />

  <!-- Main Diagram Title Header -->
  <text x="1100" y="48" class="title-main">HaqDesk AI – Knowledge Base Management Use Case Diagram</text>
  <text x="1100" y="74" class="title-sub">Standard UML 2.5 Use Case Specification · Business Knowledge Ingestion, Curation &amp; Verification</text>
  <line x1="150" y1="92" x2="2050" y2="92" stroke="#000000" stroke-width="1.2" />

  <!-- ================================================================================== -->
  <!-- SYSTEM BOUNDARY -->
  <!-- ================================================================================== -->
  <rect x="360" y="115" width="1760" height="1180" rx="14" fill="#ffffff" stroke="#000000" stroke-width="2.5" />
  <text x="390" y="152" class="boundary-title">System Boundary: HaqDesk AI – Knowledge Base Management</text>

  <!-- ================================================================================== -->
  <!-- INTERNAL PACKAGES / FUNCTIONAL SUB-DOMAINS -->
  <!-- ================================================================================== -->

  <!-- Package 1: Document Upload & Automated Ingestion Pipeline -->
  <rect x="390" y="180" width="530" height="520" class="group-box" />
  <text x="410" y="208" class="package-title">Document Ingestion Pipeline (Upload &amp; Automated Processing)</text>

  <!-- Package 2: Knowledge Catalog & Status Monitoring -->
  <rect x="945" y="180" width="550" height="520" class="group-box" />
  <text x="965" y="208" class="package-title">Knowledge Catalog &amp; Document Inspection</text>

  <!-- Package 3: Chunk Curation & Semantic Maintenance -->
  <rect x="390" y="730" width="530" height="530" class="group-box" />
  <text x="410" y="758" class="package-title">Knowledge Chunk Curation &amp; Re-Indexing</text>

  <!-- Package 4: Interactive Retrieval Verification & Testing -->
  <rect x="945" y="730" width="550" height="530" class="group-box" />
  <text x="965" y="758" class="package-title">Interactive Retrieval Verification (Test Sandbox)</text>

  <!-- Package 5: Automated Ingestion Services (Rightmost Pillar) -->
  <rect x="1525" y="180" width="570" height="1080" class="group-box" />
  <text x="1545" y="208" class="package-title">Automated Supporting Services (System Ingestion &amp; Indexing)</text>


  <!-- ================================================================================== -->
  <!-- USE CASE OVALS -->
  <!-- ================================================================================== -->

  <!-- 1. Document Upload & Ingestion -->
  <!-- UC: Access Knowledge Base -->
  <g id="UC_ACCESS_KB">
    <ellipse cx="650" cy="270" rx="160" ry="34" class="uc-oval" />
    <text x="650" y="267" class="usecase-text">Access Knowledge Base</text>
    <text x="650" y="284" class="usecase-sub">(overview, metrics &amp; catalog)</text>
  </g>

  <!-- UC: Upload Knowledge Document -->
  <g id="UC_UPLOAD_DOC">
    <ellipse cx="650" cy="410" rx="175" ry="38" class="uc-oval" stroke-width="2.2" />
    <text x="650" y="406" font-size="14.5px" font-weight="bold" fill="#000000" text-anchor="middle">Upload Knowledge Document</text>
    <text x="650" y="425" class="usecase-sub">(PDF, DOCX, TXT up to 10MB)</text>
  </g>

  <!-- UC: Delete Knowledge Document -->
  <g id="UC_DELETE_DOC">
    <ellipse cx="650" cy="550" rx="160" ry="34" class="uc-oval" />
    <text x="650" y="547" class="usecase-text">Delete Knowledge Document</text>
    <text x="650" y="564" class="usecase-sub">(cascading vector purge)</text>
  </g>


  <!-- 2. Knowledge Catalog & Status Monitoring -->
  <!-- UC: View Uploaded Documents -->
  <g id="UC_VIEW_DOCS">
    <ellipse cx="1220" cy="270" rx="165" ry="34" class="uc-oval" />
    <text x="1220" y="267" class="usecase-text">View Uploaded Documents</text>
    <text x="1220" y="284" class="usecase-sub">(file list, size, chunk counts)</text>
  </g>

  <!-- UC: View Document Details -->
  <g id="UC_VIEW_DETAILS">
    <ellipse cx="1220" cy="390" rx="160" ry="34" class="uc-oval" />
    <text x="1220" y="387" class="usecase-text">View Document Details</text>
    <text x="1220" y="404" class="usecase-sub">(metadata, file type, upload date)</text>
  </g>

  <!-- UC: View Processing Status -->
  <g id="UC_VIEW_STATUS">
    <ellipse cx="1220" cy="510" rx="160" ry="34" class="uc-oval" />
    <text x="1220" y="507" class="usecase-text">View Processing Status</text>
    <text x="1220" y="524" class="usecase-sub">(processing, ready, failed)</text>
  </g>

  <!-- UC: Search Knowledge Documents -->
  <g id="UC_SEARCH_DOCS">
    <ellipse cx="1220" cy="620" rx="155" ry="30" class="uc-oval" />
    <text x="1220" y="618" class="usecase-text">Search Knowledge Documents</text>
    <text x="1220" y="633" class="usecase-sub">(filter catalog by keyword)</text>
  </g>


  <!-- 3. Chunk Curation & Maintenance -->
  <!-- UC: Preview Knowledge Chunks -->
  <g id="UC_PREVIEW_CHUNKS">
    <ellipse cx="650" cy="830" rx="165" ry="34" class="uc-oval" />
    <text x="650" y="827" class="usecase-text">Preview Knowledge Chunks</text>
    <text x="650" y="844" class="usecase-sub">(extracted chunks &amp; page mapping)</text>
  </g>

  <!-- UC: Search Chunks -->
  <g id="UC_SEARCH_CHUNKS">
    <ellipse cx="650" cy="950" rx="155" ry="32" class="uc-oval" />
    <text x="650" y="947" class="usecase-text">Search Knowledge Chunks</text>
    <text x="650" y="964" class="usecase-sub">(in-document text filtering)</text>
  </g>

  <!-- UC: Edit Knowledge Chunk -->
  <g id="UC_EDIT_CHUNK">
    <ellipse cx="650" cy="1070" rx="170" ry="36" class="uc-oval" stroke-width="2.2" />
    <text x="650" y="1066" font-size="14px" font-weight="bold" fill="#000000" text-anchor="middle">Edit Knowledge Chunk</text>
    <text x="650" y="1084" class="usecase-sub">(inline content refinement &amp; sync)</text>
  </g>


  <!-- 4. Interactive Retrieval Testing (Test Sandbox) -->
  <!-- UC: Test Knowledge Retrieval -->
  <g id="UC_TEST_RETRIEVAL">
    <ellipse cx="1220" cy="830" rx="175" ry="38" class="uc-oval" stroke-width="2.2" />
    <text x="1220" y="826" font-size="14.5px" font-weight="bold" fill="#000000" text-anchor="middle">Test Knowledge Retrieval</text>
    <text x="1220" y="845" class="usecase-sub">(interactive question &amp; answer testing)</text>
  </g>

  <!-- UC: View Generated Test Answer -->
  <g id="UC_VIEW_ANSWER">
    <ellipse cx="1220" cy="960" rx="160" ry="34" class="uc-oval" />
    <text x="1220" y="957" class="usecase-text">View Generated Answer</text>
    <text x="1220" y="974" class="usecase-sub">(synthesized RAG response)</text>
  </g>

  <!-- UC: View Retrieved Sources & Citations -->
  <g id="UC_VIEW_SOURCES">
    <ellipse cx="1220" cy="1080" rx="165" ry="34" class="uc-oval" />
    <text x="1220" y="1077" class="usecase-text">View Retrieved Sources &amp; Citations</text>
    <text x="1220" y="1094" class="usecase-sub">(grounded document badges)</text>
  </g>

  <!-- UC: View Retrieval Confidence Score -->
  <g id="UC_VIEW_CONFIDENCE">
    <ellipse cx="1220" cy="1190" rx="160" ry="30" class="uc-oval" />
    <text x="1220" y="1188" class="usecase-text">View Confidence Match %</text>
    <text x="1220" y="1203" class="usecase-sub">(similarity percentage score)</text>
  </g>


  <!-- 5. Automated Supporting Behaviors (Right Column) -->
  <!-- UC: Validate Document -->
  <g id="UC_VALIDATE_DOC">
    <ellipse cx="1810" cy="340" rx="170" ry="36" class="uc-auto" />
    <text x="1810" y="337" class="usecase-text">Validate Document</text>
    <text x="1810" y="354" class="usecase-sub">(file extension, size &amp; non-empty check)</text>
  </g>

  <!-- UC: Process Document Content -->
  <g id="UC_PROCESS_DOC">
    <ellipse cx="1810" cy="510" rx="170" ry="38" class="uc-auto" />
    <text x="1810" y="506" class="usecase-text">Process Document Content</text>
    <text x="1810" y="524" class="usecase-sub">(text extraction &amp; QA-pair chunking)</text>
  </g>

  <!-- UC: Index Business Knowledge -->
  <g id="UC_INDEX_KNOWLEDGE">
    <ellipse cx="1810" cy="740" rx="175" ry="38" class="uc-auto" stroke-width="2.2" />
    <text x="1810" y="736" font-size="14px" font-weight="bold" fill="#000000" text-anchor="middle">Index Business Knowledge</text>
    <text x="1810" y="755" class="usecase-sub">(semantic vector embedding &amp; storage)</text>
  </g>

  <!-- UC: Purge Vector Embeddings -->
  <g id="UC_PURGE_VECTORS">
    <ellipse cx="1810" cy="940" rx="170" ry="34" class="uc-auto" />
    <text x="1810" y="937" class="usecase-text">Purge Vector Embeddings</text>
    <text x="1810" y="954" class="usecase-sub">(remove indexed points on deletion)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- ACTOR (Left Side) -->
  <!-- ================================================================================== -->
  <g id="ACTOR_ADMIN" transform="translate(180, 620)">
    <!-- Stick Figure -->
    <circle cx="0" cy="-40" r="18" fill="#ffffff" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="-22" x2="0" y2="30" stroke="#000000" stroke-width="2.4" />
    <line x1="-32" y1="-5" x2="32" y2="-5" stroke="#000000" stroke-width="2.4" />
    <line x1="0" y1="30" x2="-25" y2="78" stroke="#000000" stroke-width="2.4" />
    <line x1="0" y1="30" x2="25" y2="78" stroke="#000000" stroke-width="2.4" />
    <text x="0" y="106" class="actor-label">Business Admin</text>
    <text x="0" y="126" class="actor-sub">&lt;&lt;authorized actor&gt;&gt;</text>
    <text x="0" y="142" font-size="11px" fill="#666666" text-anchor="middle">(RBAC Verified)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- ASSOCIATIONS (Business Admin to Primary Use Cases) -->
  <!-- ================================================================================== -->
  <line x1="225" y1="580" x2="495" y2="280" class="assoc-line" /> <!-- to Access Knowledge Base -->
  <line x1="225" y1="600" x2="480" y2="410" class="assoc-line" /> <!-- to Upload Knowledge Document -->
  <line x1="225" y1="620" x2="495" y2="550" class="assoc-line" /> <!-- to Delete Knowledge Document -->
  <line x1="225" y1="640" x2="490" y2="830" class="assoc-line" /> <!-- to Preview Chunks -->
  <line x1="225" y1="660" x2="485" y2="1070" class="assoc-line" /> <!-- to Edit Chunk -->
  <line x1="225" y1="675" x2="1050" y2="830" class="assoc-line" /> <!-- to Test Knowledge Retrieval -->


  <!-- ================================================================================== -->
  <!-- UML INCLUDE & EXTEND RELATIONSHIPS -->
  <!-- ================================================================================== -->

  <!-- Access Knowledge Base Includes -->
  <!-- Access KB <<include>> View Uploaded Documents -->
  <line x1="810" y1="270" x2="1055" y2="270" class="dep-line" />
  <rect x="900" y="253" width="70" height="18" fill="#ffffff" />
  <text x="935" y="266" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- View Uploaded Documents Includes/Extends -->
  <!-- View Uploaded Documents <<include>> View Document Details -->
  <line x1="1220" y1="304" x2="1220" y2="356" class="dep-line" />
  <rect x="1185" y="322" width="70" height="16" fill="#ffffff" />
  <text x="1220" y="334" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- View Uploaded Documents <<include>> View Processing Status -->
  <path d="M 1385 270 Q 1460 380 1380 500" class="dep-line" />
  <rect x="1410" y="380" width="70" height="16" fill="#ffffff" />
  <text x="1445" y="392" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Search Documents <<extend>> View Uploaded Documents -->
  <line x1="1220" y1="590" x2="1220" y2="304" class="dep-line" />
  <rect x="1185" y="445" width="70" height="16" fill="#ffffff" />
  <text x="1220" y="457" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- Preview Chunks <<extend>> View Document Details -->
  <path d="M 815 830 Q 1020 830 1140 422" class="dep-line" />
  <rect x="965" y="625" width="70" height="16" fill="#ffffff" />
  <text x="1000" y="637" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- Search Chunks <<extend>> Preview Chunks -->
  <line x1="650" y1="918" x2="650" y2="864" class="dep-line" />
  <rect x="615" y="883" width="70" height="16" fill="#ffffff" />
  <text x="650" y="895" class="rel-text">&lt;&lt;extend&gt;&gt;</text>


  <!-- ================================================================================== -->
  <!-- AUTOMATED INGESTION & PIPELINE RELATIONSHIPS -->
  <!-- ================================================================================== -->

  <!-- Upload Document <<include>> Validate Document -->
  <path d="M 825 410 Q 1320 300 1640 340" class="dep-line" />
  <rect x="1220" y="332" width="70" height="18" fill="#ffffff" />
  <text x="1255" y="345" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Upload Document <<include>> Process Document Content -->
  <path d="M 825 425 Q 1300 480 1640 505" class="dep-line" />
  <rect x="1220" y="465" width="70" height="18" fill="#ffffff" />
  <text x="1255" y="478" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Process Document Content <<include>> Index Business Knowledge -->
  <line x1="1810" y1="548" x2="1810" y2="702" class="dep-line" />
  <rect x="1775" y="618" width="70" height="18" fill="#ffffff" />
  <text x="1810" y="631" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Edit Knowledge Chunk <<include>> Index Business Knowledge (Re-Index) -->
  <path d="M 820 1070 Q 1500 1070 1740 776" class="dep-line" />
  <rect x="1350" y="1055" width="130" height="24" fill="#ffffff" stroke="#888888" stroke-width="0.8" rx="4" />
  <text x="1415" y="1068" class="rel-text">&lt;&lt;include&gt;&gt;</text>
  <text x="1415" y="1077" class="condition-text">[Re-Index Chunk]</text>

  <!-- Delete Document <<include>> Purge Vector Embeddings -->
  <path d="M 810 550 Q 1350 720 1645 930" class="dep-line" />
  <rect x="1220" y="730" width="70" height="18" fill="#ffffff" />
  <text x="1255" y="743" class="rel-text">&lt;&lt;include&gt;&gt;</text>


  <!-- ================================================================================== -->
  <!-- RETRIEVAL TESTING (TEST SANDBOX) RELATIONSHIPS -->
  <!-- ================================================================================== -->

  <!-- Test Retrieval <<include>> View Generated Answer -->
  <line x1="1220" y1="868" x2="1220" y2="926" class="dep-line" />
  <rect x="1185" y="888" width="70" height="16" fill="#ffffff" />
  <text x="1220" y="900" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Test Retrieval <<include>> View Retrieved Sources & Citations -->
  <path d="M 1375 855 Q 1460 970 1375 1070" class="dep-line" />
  <rect x="1415" y="955" width="70" height="16" fill="#ffffff" />
  <text x="1450" y="967" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Test Retrieval <<include>> View Confidence Match % -->
  <path d="M 1390 840 Q 1495 1010 1370 1180" class="dep-line" />
  <rect x="1450" y="1010" width="70" height="16" fill="#ffffff" />
  <text x="1485" y="1022" class="rel-text">&lt;&lt;include&gt;&gt;</text>


  <!-- ================================================================================== -->
  <!-- WORKFLOW HIGHLIGHT NOTE: RBAC & BUSINESS-SPECIFIC SCOPING -->
  <!-- ================================================================================== -->
  <g transform="translate(390, 1145)">
    <rect x="0" y="0" width="530" height="115" class="legend-box" />
    <text x="20" y="24" font-size="12.5" font-weight="bold" fill="#000000">Knowledge Base Governance &amp; Security Principles:</text>
    <text x="20" y="46" font-size="11.5" fill="#222222">
      1. <tspan font-weight="bold">RBAC Isolation:</tspan> Strictly restricted to <tspan font-weight="bold">Business Admin</tspan>. Staff cannot access/mutate documents.
    </text>
    <text x="20" y="66" font-size="11.5" fill="#222222">
      2. <tspan font-weight="bold">Tenant Isolation:</tspan> All document ingestion, chunking, and vectors are partitioned by business.
    </text>
    <text x="20" y="86" font-size="11.5" fill="#222222">
      3. <tspan font-weight="bold">Live Vector Synchronization:</tspan> Chunk edits and document deletions update the vector store.
    </text>
    <text x="20" y="104" font-size="11" fill="#555555" font-style="italic">
      * Note: Low-level algorithms (chunk overlap, embedding dims, Qdrant schemas) execute behind boundary.
    </text>
  </g>

  <!-- ================================================================================== -->
  <!-- UML NOTATION LEGEND -->
  <!-- ================================================================================== -->
  <g transform="translate(945, 1260)">
    <text x="0" y="0" font-size="11" font-weight="bold" fill="#444444">UML 2.5 Notation:  —— Association   - - - &gt; &lt;&lt;include&gt;&gt; / &lt;&lt;extend&gt;&gt; Dependency   ( ) User Use Case   (- -) Automated System Use Case</text>
  </g>

</svg>
"""

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
diagram_dir = os.path.join(project_root, "docs", "diagrams", "use-case")
os.makedirs(diagram_dir, exist_ok=True)
svg_path = os.path.join(diagram_dir, "haqdesk_knowledge_base_use_case.svg")
png_path = os.path.join(diagram_dir, "haqdesk_knowledge_base_use_case.png")

with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg_code)

print(f"Saved SVG to {svg_path}")

doc = fitz.open(svg_path)
pix = doc[0].get_pixmap(dpi=300)
pix.save(png_path)
print(f"Rendered High-Res PNG to {png_path} ({pix.width}x{pix.height}px)")
