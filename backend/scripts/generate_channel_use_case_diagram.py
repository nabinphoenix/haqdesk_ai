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
      .uc-extension { fill: #ffffff; stroke: #000000; stroke-width: 1.8; stroke-dasharray: 5,4; }
      .assoc-line { stroke: #000000; stroke-width: 1.6; fill: none; }
      .dep-line { stroke: #000000; stroke-width: 1.5; stroke-dasharray: 6,4; fill: none; marker-end: url(#arrowhead); }
      .group-box { fill: #fafafa; stroke: #888888; stroke-width: 1.2; stroke-dasharray: 4,4; rx: 10; }
      .legend-box { fill: #ffffff; stroke: #666666; stroke-width: 1.2; rx: 6; }
    </style>
  </defs>

  <!-- Canvas Background -->
  <rect width="2200" height="1350" fill="#ffffff" />

  <!-- Main Diagram Title Header -->
  <text x="1100" y="48" class="title-main">HaqDesk AI – Communication Channel Integration Use Case Diagram</text>
  <text x="1100" y="74" class="title-sub">Standard UML 2.5 Specification · Active FYP Demonstrations vs. Architectural Extension Capabilities</text>
  <line x1="150" y1="92" x2="2050" y2="92" stroke="#000000" stroke-width="1.2" />

  <!-- ================================================================================== -->
  <!-- SYSTEM BOUNDARY -->
  <!-- ================================================================================== -->
  <rect x="360" y="115" width="1380" height="1180" rx="14" fill="#ffffff" stroke="#000000" stroke-width="2.5" />
  <text x="390" y="152" class="boundary-title">System Boundary: HaqDesk AI – Communication Channel Integration</text>

  <!-- ================================================================================== -->
  <!-- INTERNAL PACKAGES / FUNCTIONAL SUB-DOMAINS -->
  <!-- ================================================================================== -->

  <!-- Package 1: Integration Management & Configuration (Left Column inside boundary) -->
  <rect x="385" y="175" width="410" height="920" class="group-box" />
  <text x="405" y="202" class="package-title">Admin Integration Management &amp; Lifecycle</text>

  <!-- Package 2: Meta Channel Integration (Active FYP + Extension) -->
  <rect x="825" y="175" width="470" height="520" class="group-box" />
  <text x="845" y="202" class="package-title">Meta Platform Integration (Messenger &amp; Instagram)</text>

  <!-- Package 3: Gmail / Email Channel Integration (Active FYP) -->
  <rect x="825" y="715" width="470" height="380" class="group-box" />
  <text x="845" y="742" class="package-title">Gmail / Support Email Integration (IMAP &amp; SMTP)</text>

  <!-- Package 4: Core Operational Messaging & Synchronization -->
  <rect x="1325" y="175" width="390" height="920" class="group-box" />
  <text x="1345" y="202" class="package-title">Operational Ingestion &amp; Dispatch Engine</text>


  <!-- ================================================================================== -->
  <!-- USE CASE OVALS -->
  <!-- ================================================================================== -->

  <!-- 1. Admin Configuration & Management -->
  <!-- UC: Access Integration Settings -->
  <g id="UC_ACCESS_SETTINGS">
    <ellipse cx="590" cy="255" rx="160" ry="32" class="uc-oval" />
    <text x="590" y="252" class="usecase-text">Access Integration Settings</text>
    <text x="590" y="268" class="usecase-sub">(overview &amp; active connections)</text>
  </g>

  <!-- UC: Configure Communication Channel -->
  <g id="UC_CONFIG_CHANNEL">
    <ellipse cx="590" cy="365" rx="165" ry="34" class="uc-oval" stroke-width="2.2" />
    <text x="590" y="361" font-size="14px" font-weight="bold" fill="#000000" text-anchor="middle">Configure Communication Channel</text>
    <text x="590" y="379" class="usecase-sub">(select channel &amp; credentials)</text>
  </g>

  <!-- UC: Authenticate / Authorize Integration -->
  <g id="UC_AUTH_INTEG">
    <ellipse cx="590" cy="485" rx="165" ry="34" class="uc-oval" />
    <text x="590" y="482" class="usecase-text">Authenticate / Authorize Integration</text>
    <text x="590" y="499" class="usecase-sub">(OAuth exchange or App Password)</text>
  </g>

  <!-- UC: Verify Integration -->
  <g id="UC_VERIFY_INTEG">
    <ellipse cx="590" cy="605" rx="160" ry="34" class="uc-oval" />
    <text x="590" y="602" class="usecase-text">Verify Integration Connection</text>
    <text x="590" y="619" class="usecase-sub">(test connection &amp; validation)</text>
  </g>

  <!-- UC: View Integration Status -->
  <g id="UC_VIEW_STATUS">
    <ellipse cx="590" cy="725" rx="155" ry="32" class="uc-oval" />
    <text x="590" y="722" class="usecase-text">View Integration Status</text>
    <text x="590" y="738" class="usecase-sub">(active, page name, expiry info)</text>
  </g>

  <!-- UC: Update Integration -->
  <g id="UC_UPDATE_INTEG">
    <ellipse cx="590" cy="845" rx="155" ry="32" class="uc-oval" />
    <text x="590" y="842" class="usecase-text">Update Integration Settings</text>
    <text x="590" y="858" class="usecase-sub">(re-auth or update credentials)</text>
  </g>

  <!-- UC: Disconnect Integration -->
  <g id="UC_DISCONNECT_INTEG">
    <ellipse cx="590" cy="965" rx="160" ry="34" class="uc-oval" />
    <text x="590" y="962" class="usecase-text">Disconnect Integration</text>
    <text x="590" y="979" class="usecase-sub">(revoke credentials &amp; deactivate)</text>
  </g>


  <!-- 2. Meta Platform Specific Configuration -->
  <!-- UC: Connect Meta Integration -->
  <g id="UC_CONNECT_META">
    <ellipse cx="1060" cy="255" rx="170" ry="34" class="uc-oval" stroke-width="2.2" />
    <text x="1060" y="251" font-size="14px" font-weight="bold" fill="#000000" text-anchor="middle">Connect Meta Integration</text>
    <text x="1060" y="269" class="usecase-sub">(Facebook Page &amp; Instagram Business)</text>
  </g>

  <!-- UC: Configure Facebook Messenger (Active FYP) -->
  <g id="UC_CONFIG_FB">
    <ellipse cx="1060" cy="365" rx="165" ry="34" class="uc-oval" />
    <text x="1060" y="362" class="usecase-text">Configure Facebook Messenger</text>
    <text x="1060" y="378" class="usecase-sub">[Active FYP Demonstrated Channel]</text>
  </g>

  <!-- UC: Configure Instagram Direct (Active FYP) -->
  <g id="UC_CONFIG_IG">
    <ellipse cx="1060" cy="475" rx="165" ry="34" class="uc-oval" />
    <text x="1060" y="472" class="usecase-text">Configure Instagram Direct</text>
    <text x="1060" y="488" class="usecase-sub">[Active FYP Demonstrated Channel]</text>
  </g>

  <!-- UC: Configure WhatsApp Business (Architectural Extension) -->
  <g id="UC_CONFIG_WA">
    <ellipse cx="1060" cy="585" rx="175" ry="34" class="uc-extension" />
    <text x="1060" y="582" class="usecase-text">Configure WhatsApp Business</text>
    <text x="1060" y="598" class="usecase-sub">(Architectural Extension · Subject to Meta Verification)</text>
  </g>


  <!-- 3. Gmail / Email Specific Configuration -->
  <!-- UC: Connect Gmail -->
  <g id="UC_CONNECT_GMAIL">
    <ellipse cx="1060" cy="795" rx="170" ry="34" class="uc-oval" stroke-width="2.2" />
    <text x="1060" y="791" font-size="14px" font-weight="bold" fill="#000000" text-anchor="middle">Connect Gmail / Email Account</text>
    <text x="1060" y="809" class="usecase-sub">[Active FYP Demonstrated Channel]</text>
  </g>

  <!-- UC: Configure Email Ingestion & SMTP -->
  <g id="UC_CONFIG_EMAIL_SERVER">
    <ellipse cx="1060" cy="915" rx="165" ry="34" class="uc-oval" />
    <text x="1060" y="912" class="usecase-text">Configure Email Ingestion &amp; Dispatch</text>
    <text x="1060" y="928" class="usecase-sub">(App Password, IMAP &amp; SMTP settings)</text>
  </g>


  <!-- 4. Operational Ingestion & Dispatch Engine -->
  <!-- UC: Process Meta Communication -->
  <g id="UC_PROCESS_META">
    <ellipse cx="1520" cy="275" rx="160" ry="34" class="uc-oval" />
    <text x="1520" y="272" class="usecase-text">Process Meta Communication</text>
    <text x="1520" y="289" class="usecase-sub">(Messenger &amp; Instagram payloads)</text>
  </g>

  <!-- UC: Retrieve Gmail Messages -->
  <g id="UC_RETRIEVE_GMAIL">
    <ellipse cx="1520" cy="415" rx="160" ry="34" class="uc-oval" />
    <text x="1520" y="412" class="usecase-text">Retrieve Gmail Messages</text>
    <text x="1520" y="429" class="usecase-sub">(periodic mailbox synchronization)</text>
  </g>

  <!-- UC: Receive Customer Message -->
  <g id="UC_RECEIVE_MSG">
    <ellipse cx="1520" cy="580" rx="165" ry="36" class="uc-oval" stroke-width="2.2" />
    <text x="1520" y="576" font-size="14px" font-weight="bold" fill="#000000" text-anchor="middle">Receive Customer Message</text>
    <text x="1520" y="594" class="usecase-sub">(normalized inbound message flow)</text>
  </g>

  <!-- UC: Synchronize Customer Messages -->
  <g id="UC_SYNC_MSGS">
    <ellipse cx="1520" cy="745" rx="165" ry="34" class="uc-oval" />
    <text x="1520" y="742" class="usecase-text">Synchronize Customer Messages</text>
    <text x="1520" y="759" class="usecase-sub">(map to unified conversation thread)</text>
  </g>

  <!-- UC: Send Customer Response -->
  <g id="UC_SEND_RESP">
    <ellipse cx="1520" cy="910" rx="165" ry="36" class="uc-oval" stroke-width="2.2" />
    <text x="1520" y="906" font-size="14px" font-weight="bold" fill="#000000" text-anchor="middle">Send Customer Response</text>
    <text x="1520" y="924" class="usecase-sub">(outbound dispatch to originating channel)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- ACTORS (Left: Admin, Right: External Channel Services) -->
  <!-- ================================================================================== -->

  <!-- Primary Actor: Business Admin (Left) -->
  <g id="ACTOR_ADMIN" transform="translate(180, 560)">
    <circle cx="0" cy="-40" r="18" fill="#ffffff" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="-22" x2="0" y2="30" stroke="#000000" stroke-width="2.4" />
    <line x1="-32" y1="-5" x2="32" y2="-5" stroke="#000000" stroke-width="2.4" />
    <line x1="0" y1="30" x2="-25" y2="78" stroke="#000000" stroke-width="2.4" />
    <line x1="0" y1="30" x2="25" y2="78" stroke="#000000" stroke-width="2.4" />
    <text x="0" y="106" class="actor-label">Business Admin</text>
    <text x="0" y="126" class="actor-sub">&lt;&lt;primary actor&gt;&gt;</text>
    <text x="0" y="142" font-size="11px" fill="#666666" text-anchor="middle">(Integration Owner)</text>
  </g>

  <!-- External Actor 1: Meta Platform (Top Right) -->
  <g id="ACTOR_META" transform="translate(1950, 360)">
    <rect x="-105" y="-35" width="210" height="70" rx="8" fill="#ffffff" stroke="#000000" stroke-width="2" />
    <text x="0" y="-12" class="actor-sub">&lt;&lt;external platform&gt;&gt;</text>
    <text x="0" y="10" class="actor-label">Meta Platform</text>
    <text x="0" y="26" font-size="11px" fill="#555555" text-anchor="middle">(Messenger &amp; Instagram)</text>
  </g>

  <!-- External Actor 2: Gmail / Email Service (Bottom Right) -->
  <g id="ACTOR_GMAIL" transform="translate(1950, 830)">
    <rect x="-105" y="-35" width="210" height="70" rx="8" fill="#ffffff" stroke="#000000" stroke-width="2" />
    <text x="0" y="-12" class="actor-sub">&lt;&lt;external platform&gt;&gt;</text>
    <text x="0" y="10" class="actor-label">Gmail / Email Service</text>
    <text x="0" y="26" font-size="11px" fill="#555555" text-anchor="middle">(IMAP &amp; SMTP Infrastructure)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- ASSOCIATIONS (Actor Lines) -->
  <!-- ================================================================================== -->

  <!-- Admin to Core Management Use Cases -->
  <line x1="225" y1="520" x2="440" y2="265" class="assoc-line" /> <!-- to Access Settings -->
  <line x1="225" y1="540" x2="435" y2="365" class="assoc-line" /> <!-- to Configure Channel -->
  <line x1="225" y1="560" x2="445" y2="725" class="assoc-line" /> <!-- to View Status -->
  <line x1="225" y1="580" x2="445" y2="845" class="assoc-line" /> <!-- to Update Integration -->
  <line x1="225" y1="600" x2="440" y2="965" class="assoc-line" /> <!-- to Disconnect Integration -->

  <!-- Meta Platform Associations -->
  <line x1="1845" y1="360" x2="1680" y2="275" class="assoc-line" /> <!-- Meta -> Process Meta -->
  <line x1="1845" y1="375" x2="1685" y2="570" class="assoc-line" /> <!-- Meta -> Receive Customer Msg -->
  <line x1="1845" y1="390" x2="1685" y2="900" class="assoc-line" /> <!-- Meta -> Send Customer Response -->

  <!-- Gmail Service Associations -->
  <line x1="1845" y1="820" x2="1680" y2="425" class="assoc-line" /> <!-- Gmail -> Retrieve Gmail -->
  <line x1="1845" y1="835" x2="1685" y2="600" class="assoc-line" /> <!-- Gmail -> Receive Customer Msg -->
  <line x1="1845" y1="850" x2="1685" y2="925" class="assoc-line" /> <!-- Gmail -> Send Customer Response -->


  <!-- ================================================================================== -->
  <!-- UML INCLUDE & EXTEND RELATIONSHIPS -->
  <!-- ================================================================================== -->

  <!-- Admin Workflow Inclusions -->
  <!-- Access Settings <<include>> View Status -->
  <path d="M 590 287 L 590 693" class="dep-line" />
  <rect x="555" y="420" width="70" height="16" fill="#ffffff" />
  <text x="590" y="432" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Configure Channel <<include>> Authenticate/Authorize -->
  <line x1="590" y1="399" x2="590" y2="451" class="dep-line" />
  <rect x="555" y="418" width="70" height="16" fill="#ffffff" />
  <text x="590" y="430" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Configure Channel <<include>> Verify Integration -->
  <path d="M 430 380 Q 320 500 435 595" class="dep-line" />
  <rect x="335" y="488" width="70" height="16" fill="#ffffff" />
  <text x="370" y="500" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Meta Connection Specializations / Extensions -->
  <!-- Connect Meta <<extend>> Configure Communication Channel -->
  <line x1="895" y1="270" x2="745" y2="350" class="dep-line" />
  <rect x="785" y="300" width="66" height="16" fill="#ffffff" />
  <text x="818" y="312" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- Configure Messenger <<include>> Connect Meta -->
  <line x1="1060" y1="331" x2="1060" y2="289" class="dep-line" />
  <rect x="1025" y="302" width="70" height="16" fill="#ffffff" />
  <text x="1060" y="314" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Configure Instagram <<include>> Connect Meta -->
  <path d="M 1215 460 Q 1280 360 1210 275" class="dep-line" />
  <rect x="1225" y="360" width="70" height="16" fill="#ffffff" />
  <text x="1260" y="372" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Configure WhatsApp <<extend>> Connect Meta (Architectural Extension) -->
  <path d="M 910 570 Q 820 440 915 285" class="dep-line" />
  <rect x="800" y="430" width="130" height="26" fill="#ffffff" stroke="#888888" stroke-width="0.8" rx="4" />
  <text x="865" y="443" class="rel-text">&lt;&lt;extend&gt;&gt;</text>
  <text x="865" y="453" class="condition-text">[Eligible Extension]</text>

  <!-- Gmail Connection Specializations / Extensions -->
  <!-- Connect Gmail <<extend>> Configure Communication Channel -->
  <path d="M 895 780 Q 750 600 740 395" class="dep-line" />
  <rect x="760" y="580" width="66" height="16" fill="#ffffff" />
  <text x="793" y="592" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- Connect Gmail <<include>> Configure Email Ingestion & SMTP -->
  <line x1="1060" y1="829" x2="1060" y2="881" class="dep-line" />
  <rect x="1025" y="848" width="70" height="16" fill="#ffffff" />
  <text x="1060" y="860" class="rel-text">&lt;&lt;include&gt;&gt;</text>


  <!-- Operational Pipeline Relationships -->
  <!-- Receive Customer Message <<include>> Process Meta Communication -->
  <path d="M 1490 545 Q 1420 420 1480 305" class="dep-line" />
  <rect x="1410" y="415" width="70" height="16" fill="#ffffff" />
  <text x="1445" y="427" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Receive Customer Message <<include>> Retrieve Gmail Messages -->
  <line x1="1520" y1="544" x2="1520" y2="449" class="dep-line" />
  <rect x="1485" y="488" width="70" height="16" fill="#ffffff" />
  <text x="1520" y="500" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Receive Customer Message <<include>> Synchronize Customer Messages -->
  <line x1="1520" y1="616" x2="1520" y2="711" class="dep-line" />
  <rect x="1485" y="655" width="70" height="16" fill="#ffffff" />
  <text x="1520" y="667" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Send Customer Response <<include>> Synchronize Customer Messages -->
  <line x1="1520" y1="874" x2="1520" y2="779" class="dep-line" />
  <rect x="1485" y="818" width="70" height="16" fill="#ffffff" />
  <text x="1520" y="830" class="rel-text">&lt;&lt;include&gt;&gt;</text>


  <!-- ================================================================================== -->
  <!-- ARCHITECTURAL DISTINCTION NOTE (Bottom) -->
  <!-- ================================================================================== -->
  <g transform="translate(385, 1115)">
    <rect x="0" y="0" width="1330" height="150" class="legend-box" />
    <text x="25" y="26" font-size="13.5" font-weight="bold" fill="#000000">FYP Demonstration Scope vs. Omnichannel Extensibility Architecture:</text>
    
    <text x="25" y="52" font-size="12" fill="#222222">
      • <tspan font-weight="bold">Actively Demonstrated FYP Channels:</tspan> <tspan font-weight="bold">Facebook Messenger</tspan>, <tspan font-weight="bold">Instagram Direct</tspan> (via Meta Page OAuth &amp; Webhooks), and <tspan font-weight="bold">Gmail</tspan> (via IMAP &amp; SMTP).
    </text>
    <text x="25" y="74" font-size="12" fill="#222222">
      • <tspan font-weight="bold">Architectural Extension Capability:</tspan> The data model and ingestion pipeline natively support <tspan font-weight="bold">WhatsApp Business</tspan> and generic channels.
    </text>
    <text x="25" y="96" font-size="12" fill="#222222">
      • <tspan font-weight="bold">Platform Permission Boundary:</tspan> The Meta test environment is non-business-verified; WhatsApp Business requires official Meta Business Verification and permissions.
    </text>
    <text x="25" y="118" font-size="12" fill="#444444" font-style="italic">
      * Note: Additional eligible channels are subject to business verification and platform permissions; they are represented as dashed extension elements.
    </text>
  </g>

  <!-- ================================================================================== -->
  <!-- UML NOTATION LEGEND -->
  <!-- ================================================================================== -->
  <g transform="translate(385, 1275)">
    <text x="0" y="0" font-size="11" font-weight="bold" fill="#444444">UML 2.5 Notation:  —— Association   - - - &gt; &lt;&lt;include&gt;&gt; / &lt;&lt;extend&gt;&gt; Dependency   ( ) Active FYP Channel   (- -) Eligible Architectural Extension</text>
  </g>

</svg>
"""

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
diagram_dir = os.path.join(project_root, "docs", "diagrams", "use-case")
os.makedirs(diagram_dir, exist_ok=True)
svg_path = os.path.join(diagram_dir, "haqdesk_channel_integration_use_case.svg")
png_path = os.path.join(diagram_dir, "haqdesk_channel_integration_use_case.png")

with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg_code)

print(f"Saved SVG to {svg_path}")

doc = fitz.open(svg_path)
pix = doc[0].get_pixmap(dpi=300)
pix.save(png_path)
print(f"Rendered High-Res PNG to {png_path} ({pix.width}x{pix.height}px)")
