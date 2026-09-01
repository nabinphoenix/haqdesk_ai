import fitz
import os

svg_code = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2200 1350" width="2200" height="1350" style="background-color: #ffffff; font-family: 'Arial', 'Helvetica Neue', sans-serif;">
  <defs>
    <!-- UML Markers -->
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#000000" />
    </marker>
    <marker id="generalization" markerWidth="14" markerHeight="12" refX="13" refY="6" orient="auto">
      <polygon points="0 0, 13 6, 0 12" fill="#ffffff" stroke="#000000" stroke-width="1.6" />
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
      .assoc-line { stroke: #000000; stroke-width: 1.6; fill: none; }
      .dep-line { stroke: #000000; stroke-width: 1.5; stroke-dasharray: 6,4; fill: none; marker-end: url(#arrowhead); }
      .gen-line { stroke: #000000; stroke-width: 1.8; fill: none; marker-end: url(#generalization); }
      .group-box { fill: #fafafa; stroke: #888888; stroke-width: 1.2; stroke-dasharray: 4,4; rx: 10; }
      .legend-box { fill: #ffffff; stroke: #666666; stroke-width: 1.2; rx: 6; }
    </style>
  </defs>

  <!-- Canvas Background -->
  <rect width="2200" height="1350" fill="#ffffff" />

  <!-- Main Diagram Title Header (No Figure numbers inside image) -->
  <text x="1100" y="48" class="title-main">Overall Use Case Diagram of HaqDesk AI</text>
  <text x="1100" y="74" class="title-sub">Standard UML 2.5 Specification · System Boundary, Core Actors &amp; Major Functional Capabilities</text>
  <line x1="150" y1="92" x2="2050" y2="92" stroke="#000000" stroke-width="1.2" />

  <!-- ================================================================================== -->
  <!-- SYSTEM BOUNDARY -->
  <!-- ================================================================================== -->
  <rect x="360" y="115" width="1380" height="1180" rx="14" fill="#ffffff" stroke="#000000" stroke-width="2.5" />
  <text x="390" y="152" class="boundary-title">System Boundary: HaqDesk AI</text>

  <!-- ================================================================================== -->
  <!-- INTERNAL PACKAGES / FUNCTIONAL SUB-DOMAINS -->
  <!-- ================================================================================== -->

  <!-- Package 1: Business Administration & Management (Top-Left) -->
  <rect x="385" y="175" width="410" height="490" class="group-box" />
  <text x="405" y="202" class="package-title">Business Administration &amp; Setup</text>

  <!-- Package 2: Customer Support & Unified Inbox Workspace (Bottom-Left) -->
  <rect x="385" y="685" width="410" height="425" class="group-box" />
  <text x="405" y="712" class="package-title">Customer Support &amp; Unified Inbox</text>

  <!-- Package 3: AI Intelligence Engine (Top-Right of Center) -->
  <rect x="825" y="175" width="470" height="490" class="group-box" />
  <text x="845" y="202" class="package-title">AI Intelligence &amp; Human-in-the-Loop</text>

  <!-- Package 4: Collaboration & Business Insights (Bottom-Right of Center) -->
  <rect x="825" y="685" width="470" height="425" class="group-box" />
  <text x="845" y="712" class="package-title">Collaboration &amp; Business Intelligence</text>

  <!-- Package 5: External Channel Ingestion & Delivery Hub (Rightmost) -->
  <rect x="1325" y="175" width="390" height="935" class="group-box" />
  <text x="1345" y="202" class="package-title">Channel Ingestion &amp; Dispatch</text>


  <!-- ================================================================================== -->
  <!-- USE CASE OVALS -->
  <!-- ================================================================================== -->

  <!-- Package 1: Administration & Setup -->
  <!-- UC: Register Business Account -->
  <g id="UC_REGISTER">
    <ellipse cx="590" cy="250" rx="160" ry="30" class="uc-oval" />
    <text x="590" y="248" class="usecase-text">Register Business Account</text>
    <text x="590" y="263" class="usecase-sub">(onboarding &amp; tenant creation)</text>
  </g>

  <!-- UC: Log In / Authenticate -->
  <g id="UC_LOGIN">
    <ellipse cx="590" cy="330" rx="155" ry="30" class="uc-oval" />
    <text x="590" y="328" class="usecase-text">Log In / Authenticate</text>
    <text x="590" y="343" class="usecase-sub">(email/password &amp; Google OAuth)</text>
  </g>

  <!-- UC: Manage Business Profile & Settings -->
  <g id="UC_PROFILE_SETTINGS">
    <ellipse cx="590" cy="415" rx="165" ry="32" class="uc-oval" />
    <text x="590" y="412" class="usecase-text">Manage Business Profile &amp; Settings</text>
    <text x="590" y="428" class="usecase-sub">(profile info &amp; AI response mode)</text>
  </g>

  <!-- UC: Manage Staff -->
  <g id="UC_STAFF">
    <ellipse cx="590" cy="500" rx="155" ry="30" class="uc-oval" />
    <text x="590" y="498" class="usecase-text">Manage Staff</text>
    <text x="590" y="513" class="usecase-sub">(invite, roles &amp; team access)</text>
  </g>

  <!-- UC: Configure Communication Integrations -->
  <g id="UC_INTEG">
    <ellipse cx="590" cy="585" rx="170" ry="32" class="uc-oval" />
    <text x="590" y="582" class="usecase-text">Configure Communication Integrations</text>
    <text x="590" y="598" class="usecase-sub">(Meta Messenger, Instagram, Gmail)</text>
  </g>

  <!-- UC: Manage Knowledge Base -->
  <g id="UC_KB">
    <ellipse cx="590" cy="660" rx="160" ry="30" class="uc-oval" />
    <text x="590" y="658" class="usecase-text">Manage Knowledge Base</text>
    <text x="590" y="673" class="usecase-sub">(upload, chunk curation &amp; test)</text>
  </g>


  <!-- Package 2: Customer Support & Unified Inbox Workspace -->
  <!-- UC: Access Unified Inbox -->
  <g id="UC_INBOX">
    <ellipse cx="590" cy="760" rx="160" ry="32" class="uc-oval" />
    <text x="590" y="757" class="usecase-text">Access Unified Inbox</text>
    <text x="590" y="773" class="usecase-sub">(omnichannel customer feed)</text>
  </g>

  <!-- UC: Manage Customer Conversations -->
  <g id="UC_CONV">
    <ellipse cx="590" cy="855" rx="170" ry="34" class="uc-oval" stroke-width="2.2" />
    <text x="590" y="851" font-size="14px" font-weight="bold" fill="#000000" text-anchor="middle">Manage Customer Conversations</text>
    <text x="590" y="869" class="usecase-sub">(history, customer context &amp; sentiment)</text>
  </g>

  <!-- UC: Write Manual Response -->
  <g id="UC_MANUAL_RESP">
    <ellipse cx="590" cy="955" rx="160" ry="32" class="uc-oval" />
    <text x="590" y="952" class="usecase-text">Write Manual Response</text>
    <text x="590" y="968" class="usecase-sub">(text composer, files &amp; voice note)</text>
  </g>

  <!-- UC: Send Customer Response -->
  <g id="UC_SEND_RESP">
    <ellipse cx="590" cy="1050" rx="165" ry="34" class="uc-oval" stroke-width="2.2" />
    <text x="590" y="1046" font-size="14px" font-weight="bold" fill="#000000" text-anchor="middle">Send Customer Response</text>
    <text x="590" y="1064" class="usecase-sub">(human authorized message send)</text>
  </g>


  <!-- Package 3: AI Intelligence Engine -->
  <!-- UC: Generate AI-Assisted Response -->
  <g id="UC_GEN_AI">
    <ellipse cx="1060" cy="270" rx="180" ry="38" class="uc-oval" stroke-width="2.2" />
    <text x="1060" y="266" font-size="14.5px" font-weight="bold" fill="#000000" text-anchor="middle">Generate AI-Assisted Response</text>
    <text x="1060" y="285" class="usecase-sub">(RAG context retrieval &amp; draft reply)</text>
  </g>

  <!-- UC: Retrieve Business Knowledge -->
  <g id="UC_RETRIEVE_KB">
    <ellipse cx="1060" cy="400" rx="170" ry="34" class="uc-oval" />
    <text x="1060" y="397" class="usecase-text">Retrieve Business Knowledge</text>
    <text x="1060" y="414" class="usecase-sub">(semantic search in business index)</text>
  </g>

  <!-- UC: Review AI Draft -->
  <g id="UC_REVIEW_AI">
    <ellipse cx="1060" cy="530" rx="165" ry="34" class="uc-oval" />
    <text x="1060" y="527" class="usecase-text">Review AI Draft</text>
    <text x="1060" y="544" class="usecase-sub">(inspect sources &amp; match score)</text>
  </g>

  <!-- UC: Accept / Edit / Reject AI Draft -->
  <g id="UC_DECIDE_AI">
    <ellipse cx="1060" cy="640" rx="170" ry="34" class="uc-oval" />
    <text x="1060" y="637" class="usecase-text">Accept / Edit / Reject AI Draft</text>
    <text x="1060" y="654" class="usecase-sub">(Human-in-the-Loop decision)</text>
  </g>


  <!-- Package 4: Collaboration & Analytics -->
  <!-- UC: Use Internal Team Chat -->
  <g id="UC_INTERNAL_CHAT">
    <ellipse cx="1060" cy="780" rx="165" ry="34" class="uc-oval" />
    <text x="1060" y="777" class="usecase-text">Use Internal Team Chat</text>
    <text x="1060" y="794" class="usecase-sub">(direct messaging &amp; presence)</text>
  </g>

  <!-- UC: View Analytics -->
  <g id="UC_VIEW_ANALYTICS">
    <ellipse cx="1060" cy="920" rx="165" ry="34" class="uc-oval" />
    <text x="1060" y="917" class="usecase-text">View Analytics</text>
    <text x="1060" y="934" class="usecase-sub">(volume, response times &amp; sentiment)</text>
  </g>

  <!-- UC: Export Analytics Report -->
  <g id="UC_EXPORT_ANALYTICS">
    <ellipse cx="1060" cy="1030" rx="155" ry="30" class="uc-oval" />
    <text x="1060" y="1028" class="usecase-text">Export Analytics Report</text>
    <text x="1060" y="1043" class="usecase-sub">(CSV / PDF summary download)</text>
  </g>


  <!-- Package 5: Channel Ingestion & Dispatch Engine -->
  <!-- UC: Deliver Incoming Customer Message -->
  <g id="UC_DELIVER_IN">
    <ellipse cx="1520" cy="340" rx="165" ry="36" class="uc-oval" />
    <text x="1520" y="337" class="usecase-text">Deliver Incoming Customer Message</text>
    <text x="1520" y="354" class="usecase-sub">(inbound webhook &amp; IMAP ingestion)</text>
  </g>

  <!-- UC: Deliver Outgoing Business Response -->
  <g id="UC_DELIVER_OUT">
    <ellipse cx="1520" cy="850" rx="165" ry="36" class="uc-oval" />
    <text x="1520" y="847" class="usecase-text">Deliver Outgoing Business Response</text>
    <text x="1520" y="864" class="usecase-sub">(Meta Send API &amp; SMTP dispatch)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- EXTERNAL USE CASES (Outside boundary) -->
  <!-- ================================================================================== -->
  <g id="UC_SEND_MSG">
    <ellipse cx="1940" cy="340" rx="145" ry="34" class="uc-oval" />
    <text x="1940" y="337" class="usecase-text">Send Message to Business</text>
    <text x="1940" y="353" class="usecase-sub">(via customer channel)</text>
  </g>

  <g id="UC_RECV_RESP">
    <ellipse cx="1940" cy="850" rx="145" ry="34" class="uc-oval" />
    <text x="1940" y="847" class="usecase-text">Receive Business Response</text>
    <text x="1940" y="863" class="usecase-sub">(in native channel thread)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- ACTORS -->
  <!-- ================================================================================== -->

  <!-- Primary Actor 1: Support Staff (Left) -->
  <g id="ACTOR_STAFF" transform="translate(180, 830)">
    <circle cx="0" cy="-35" r="16" fill="#ffffff" stroke="#000000" stroke-width="2" />
    <line x1="0" y1="-19" x2="0" y2="25" stroke="#000000" stroke-width="2.2" />
    <line x1="-28" y1="-5" x2="28" y2="-5" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="-22" y2="65" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="22" y2="65" stroke="#000000" stroke-width="2.2" />
    <text x="0" y="90" class="actor-label">Support Staff</text>
    <text x="0" y="108" class="actor-sub">&lt;&lt;primary actor&gt;&gt; / Agent</text>
  </g>

  <!-- Primary Actor 2: Business Admin (Left, Generalizes Support Staff) -->
  <g id="ACTOR_ADMIN" transform="translate(180, 360)">
    <circle cx="0" cy="-35" r="16" fill="#ffffff" stroke="#000000" stroke-width="2" />
    <line x1="0" y1="-19" x2="0" y2="25" stroke="#000000" stroke-width="2.2" />
    <line x1="-28" y1="-5" x2="28" y2="-5" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="-22" y2="65" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="22" y2="65" stroke="#000000" stroke-width="2.2" />
    <text x="0" y="90" class="actor-label">Business Admin</text>
    <text x="0" y="108" class="actor-sub">&lt;&lt;primary actor&gt;&gt; / Manager</text>
  </g>

  <!-- Actor Generalization Line: Business Admin -> Support Staff -->
  <line x1="180" y1="460" x2="180" y2="735" class="gen-line" />
  <rect x="125" y="585" width="110" height="22" fill="#ffffff" stroke="#888888" stroke-width="0.8" rx="4" />
  <text x="180" y="600" font-size="11" font-weight="bold" fill="#000000" text-anchor="middle">&lt;&lt;generalizes&gt;&gt;</text>

  <!-- External Actor 1: Customer / End User (Far Right) -->
  <g id="ACTOR_CUSTOMER" transform="translate(2020, 595)">
    <circle cx="0" cy="-35" r="16" fill="#ffffff" stroke="#000000" stroke-width="2" />
    <line x1="0" y1="-19" x2="0" y2="25" stroke="#000000" stroke-width="2.2" />
    <line x1="-28" y1="-5" x2="28" y2="-5" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="-22" y2="65" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="22" y2="65" stroke="#000000" stroke-width="2.2" />
    <text x="0" y="90" class="actor-label">Customer / End User</text>
    <text x="0" y="108" class="actor-sub">&lt;&lt;external actor&gt;&gt;</text>
  </g>

  <!-- External Actor 2: Communication Platform (Bottom Right) -->
  <g id="ACTOR_PLATFORM" transform="translate(1520, 1170)">
    <rect x="-110" y="-35" width="220" height="70" rx="8" fill="#ffffff" stroke="#000000" stroke-width="2" />
    <text x="0" y="-12" class="actor-sub">&lt;&lt;external platform&gt;&gt;</text>
    <text x="0" y="10" class="actor-label">Communication Platform</text>
    <text x="0" y="26" font-size="11px" fill="#555555" text-anchor="middle">(Meta, Gmail, WhatsApp)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- ASSOCIATIONS (Actor to Use Case Lines) -->
  <!-- ================================================================================== -->

  <!-- Business Admin Specific Associations -->
  <line x1="215" y1="310" x2="440" y2="250" class="assoc-line" /> <!-- to Register -->
  <line x1="215" y1="330" x2="445" y2="330" class="assoc-line" /> <!-- to Login -->
  <line x1="215" y1="350" x2="435" y2="415" class="assoc-line" /> <!-- to Profile Settings -->
  <line x1="215" y1="370" x2="440" y2="500" class="assoc-line" /> <!-- to Staff -->
  <line x1="215" y1="390" x2="430" y2="585" class="assoc-line" /> <!-- to Integrations -->
  <line x1="215" y1="410" x2="440" y2="660" class="assoc-line" /> <!-- to Knowledge Base -->

  <!-- Support Staff Associations (Inherited by Business Admin) -->
  <line x1="215" y1="780" x2="445" y2="340" class="assoc-line" /> <!-- Staff to Login -->
  <line x1="215" y1="800" x2="440" y2="760" class="assoc-line" /> <!-- to Unified Inbox -->
  <line x1="215" y1="820" x2="430" y2="855" class="assoc-line" /> <!-- to Manage Conversations -->
  <line x1="215" y1="840" x2="440" y2="955" class="assoc-line" /> <!-- to Write Manual Response -->
  <line x1="215" y1="860" x2="435" y2="1050" class="assoc-line" /> <!-- to Send Response -->
  <line x1="215" y1="875" x2="905" y2="530" class="assoc-line" /> <!-- to Review AI Draft -->
  <line x1="215" y1="885" x2="900" y2="640" class="assoc-line" /> <!-- to Accept/Edit/Reject -->
  <line x1="215" y1="895" x2="905" y2="780" class="assoc-line" /> <!-- to Internal Chat -->
  <line x1="215" y1="905" x2="905" y2="920" class="assoc-line" /> <!-- to View Analytics -->

  <!-- Customer Associations -->
  <line x1="1980" y1="550" x2="1940" y2="375" class="assoc-line" /> <!-- Customer -> Send Message -->
  <line x1="1980" y1="640" x2="1940" y2="815" class="assoc-line" /> <!-- Customer -> Receive Response -->

  <!-- Communication Platform Associations -->
  <line x1="1520" y1="1135" x2="1520" y2="376" class="assoc-line" /> <!-- Platform -> Deliver Incoming -->
  <line x1="1520" y1="1135" x2="1520" y2="886" class="assoc-line" /> <!-- Platform -> Deliver Outgoing -->


  <!-- ================================================================================== -->
  <!-- UML INCLUDE & EXTEND RELATIONSHIPS -->
  <!-- ================================================================================== -->

  <!-- Inbound Flow -->
  <!-- Send Message <<include>> Deliver Incoming Message -->
  <line x1="1795" y1="340" x2="1685" y2="340" class="dep-line" />
  <rect x="1710" y="323" width="70" height="18" fill="#ffffff" />
  <text x="1745" y="336" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Deliver Incoming <<include>> Generate AI Response -->
  <line x1="1355" y1="320" x2="1240" y2="280" class="dep-line" />
  <rect x="1265" y="285" width="70" height="18" fill="#ffffff" />
  <text x="1300" y="298" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Deliver Incoming <<include>> Manage Conversations (Updates conversation feed) -->
  <path d="M 1430 376 Q 1000 680 755 830" class="dep-line" />
  <rect x="1065" y="615" width="70" height="18" fill="#ffffff" />
  <text x="1100" y="628" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- AI Intelligence Core Relationships -->
  <!-- Generate AI Response <<include>> Retrieve Business Knowledge -->
  <line x1="1060" y1="308" x2="1060" y2="366" class="dep-line" />
  <rect x="1025" y="330" width="70" height="18" fill="#ffffff" />
  <text x="1060" y="343" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Review AI Draft <<extend>> Generate AI-Assisted Response [Review Mode] -->
  <line x1="1060" y1="496" x2="1060" y2="308" class="dep-line" />
  <rect x="990" y="430" width="140" height="28" fill="#ffffff" stroke="#888888" stroke-width="0.8" rx="4" />
  <text x="1060" y="443" class="rel-text">&lt;&lt;extend&gt;&gt;</text>
  <text x="1060" y="455" class="condition-text">[Review Mode active]</text>

  <!-- Accept/Edit/Reject <<include>> Review AI Draft -->
  <line x1="1060" y1="606" x2="1060" y2="564" class="dep-line" />
  <rect x="1025" y="578" width="70" height="16" fill="#ffffff" />
  <text x="1060" y="590" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Response Dispatch Flow -->
  <!-- Write Manual Response <<extend>> Send Customer Response -->
  <line x1="590" y1="987" x2="590" y2="1016" class="dep-line" />
  <rect x="555" y="995" width="70" height="16" fill="#ffffff" />
  <text x="590" y="1007" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- Send Customer Response <<include>> Deliver Outgoing Response -->
  <path d="M 755 1050 Q 1100 1050 1355 870" class="dep-line" />
  <rect x="1020" y="975" width="70" height="18" fill="#ffffff" />
  <text x="1055" y="988" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Deliver Outgoing Response <<include>> Receive Business Response -->
  <line x1="1685" y1="850" x2="1795" y2="850" class="dep-line" />
  <rect x="1710" y="833" width="70" height="18" fill="#ffffff" />
  <text x="1745" y="846" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Analytics Export Extension -->
  <!-- Export Report <<extend>> View Analytics -->
  <line x1="1060" y1="1000" x2="1060" y2="954" class="dep-line" />
  <rect x="1025" y="970" width="70" height="16" fill="#ffffff" />
  <text x="1060" y="982" class="rel-text">&lt;&lt;extend&gt;&gt;</text>


  <!-- ================================================================================== -->
  <!-- WORKFLOW HIGHLIGHT NOTE: ARCHITECTURAL SUMMARY -->
  <!-- ================================================================================== -->
  <g transform="translate(385, 1125)">
    <rect x="0" y="0" width="1330" height="135" class="legend-box" />
    <text x="25" y="24" font-size="13.5" font-weight="bold" fill="#000000">HaqDesk AI Core Architectural Capabilities &amp; Governance Model:</text>
    
    <text x="25" y="48" font-size="12" fill="#222222">
      1. <tspan font-weight="bold">Role-Based Access Control (RBAC):</tspan> <tspan font-weight="bold">Business Admin</tspan> configures settings, staff, channels, and knowledge base; <tspan font-weight="bold">Support Staff</tspan> handles inbox operations.
    </text>
    <text x="25" y="70" font-size="12" fill="#222222">
      2. <tspan font-weight="bold">Human-in-the-Loop AI Assistant:</tspan> RAG synthesizes draft replies from tenant documents, requiring human oversight (<tspan font-weight="bold">Accept / Edit / Reject</tspan>) before dispatch.
    </text>
    <text x="25" y="92" font-size="12" fill="#222222">
      3. <tspan font-weight="bold">Omnichannel Unified Feed:</tspan> Messages from Meta (Messenger &amp; Instagram) and Gmail synchronize into one real-time multi-tenant workspace.
    </text>
    <text x="25" y="112" font-size="11.5" fill="#555555" font-style="italic">
      * External customers interact strictly via messaging platforms outside the HaqDesk authentication perimeter.
    </text>
  </g>

  <!-- ================================================================================== -->
  <!-- UML NOTATION LEGEND -->
  <!-- ================================================================================== -->
  <g transform="translate(385, 1270)">
    <text x="0" y="0" font-size="11" font-weight="bold" fill="#444444">UML 2.5 Notation:  —— Association   - - - &gt; &lt;&lt;include&gt;&gt; / &lt;&lt;extend&gt;&gt; Dependency   ———▷ Generalization   ( ) Use Case</text>
  </g>

</svg>
"""

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
diagram_dir = os.path.join(project_root, "docs", "diagrams", "use-case")
os.makedirs(diagram_dir, exist_ok=True)
svg_path = os.path.join(diagram_dir, "haqdesk_overall_use_case.svg")
png_path = os.path.join(diagram_dir, "haqdesk_overall_use_case.png")

with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg_code)

print(f"Saved SVG to {svg_path}")

doc = fitz.open(svg_path)
pix = doc[0].get_pixmap(dpi=300)
pix.save(png_path)
print(f"Rendered High-Res PNG to {png_path} ({pix.width}x{pix.height}px)")
