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
      .actor-label { font-size: 15px; font-weight: bold; fill: #000000; text-anchor: middle; }
      .actor-sub { font-size: 12px; fill: #555555; text-anchor: middle; font-style: italic; }
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

  <!-- Main Diagram Title Header -->
  <text x="1100" y="48" class="title-main">HaqDesk AI – AI-Assisted Response &amp; RAG Use Case Diagram</text>
  <text x="1100" y="74" class="title-sub">Standard UML 2.5 Use Case Specification · Knowledge Retrieval &amp; Human-in-the-Loop Governance</text>
  <line x1="150" y1="92" x2="2050" y2="92" stroke="#000000" stroke-width="1.2" />

  <!-- ================================================================================== -->
  <!-- SYSTEM BOUNDARY -->
  <!-- ================================================================================== -->
  <rect x="360" y="115" width="1380" height="1180" rx="14" fill="#ffffff" stroke="#000000" stroke-width="2.5" />
  <text x="390" y="152" class="boundary-title">System Boundary: HaqDesk AI – AI-Assisted Customer Response</text>

  <!-- ================================================================================== -->
  <!-- INTERNAL PACKAGES / FUNCTIONAL SUB-DOMAINS -->
  <!-- ================================================================================== -->

  <!-- Package 1: Knowledge Retrieval & Context Synthesis -->
  <rect x="385" y="175" width="410" height="490" class="group-box" />
  <text x="405" y="202" class="package-title">Knowledge Retrieval &amp; Context Assembly</text>

  <!-- Package 2: Suggestion Inspection & Intelligence Context -->
  <rect x="385" y="685" width="410" height="425" class="group-box" />
  <text x="405" y="712" class="package-title">Metadata, Confidence &amp; Explainability</text>

  <!-- Package 3: Central AI Orchestration -->
  <rect x="825" y="175" width="470" height="490" class="group-box" />
  <text x="845" y="202" class="package-title">Central AI Response Generation</text>

  <!-- Package 4: Human-in-the-Loop Review & Decision -->
  <rect x="825" y="685" width="470" height="585" class="group-box" />
  <text x="845" y="712" class="package-title">Human-in-the-Loop Review &amp; Decision</text>

  <!-- Package 5: Channel Ingestion & Delivery -->
  <rect x="1325" y="175" width="390" height="935" class="group-box" />
  <text x="1345" y="202" class="package-title">Channel Ingestion &amp; Dispatch Hub</text>


  <!-- ================================================================================== -->
  <!-- USE CASE OVALS -->
  <!-- ================================================================================== -->

  <!-- Package 1: Knowledge & Context Retrieval -->
  <!-- UC: Retrieve Relevant Business Knowledge -->
  <g id="UC_RETRIEVE_KB">
    <ellipse cx="590" cy="270" rx="165" ry="34" class="uc-oval" />
    <text x="590" y="267" class="usecase-text">Retrieve Relevant Business Knowledge</text>
    <text x="590" y="284" class="usecase-sub">(semantic search on knowledge base)</text>
  </g>

  <!-- UC: Use Conversation Context -->
  <g id="UC_USE_CONTEXT">
    <ellipse cx="590" cy="390" rx="165" ry="34" class="uc-oval" />
    <text x="590" y="387" class="usecase-text">Use Conversation Context</text>
    <text x="590" y="404" class="usecase-sub">(multi-turn chat memory &amp; customer name)</text>
  </g>

  <!-- UC: Generate AI Response Draft -->
  <g id="UC_GEN_DRAFT">
    <ellipse cx="590" cy="510" rx="165" ry="34" class="uc-oval" />
    <text x="590" y="507" class="usecase-text">Generate AI Response Draft</text>
    <text x="590" y="524" class="usecase-sub">(prompt synthesis &amp; signature formatting)</text>
  </g>

  <!-- UC: Test Knowledge Retrieval (Admin) -->
  <g id="UC_TEST_RETRIEVAL">
    <ellipse cx="590" cy="615" rx="155" ry="30" class="uc-oval" />
    <text x="590" y="613" class="usecase-text">Test Knowledge Retrieval</text>
    <text x="590" y="628" class="usecase-sub">(interactive knowledge base testing)</text>
  </g>


  <!-- Package 2: Metadata & Inspection -->
  <!-- UC: Display Retrieved Sources -->
  <g id="UC_DISPLAY_SOURCES">
    <ellipse cx="590" cy="770" rx="160" ry="32" class="uc-oval" />
    <text x="590" y="767" class="usecase-text">Display Retrieved Sources</text>
    <text x="590" y="784" class="usecase-sub">(grounded document citation badges)</text>
  </g>

  <!-- UC: Display Confidence / Similarity Information -->
  <g id="UC_DISPLAY_CONFIDENCE">
    <ellipse cx="590" cy="880" rx="165" ry="32" class="uc-oval" />
    <text x="590" y="877" class="usecase-text">Display Confidence / Similarity Info</text>
    <text x="590" y="894" class="usecase-sub">(percentage match indicator)</text>
  </g>

  <!-- UC: View Sentiment / Language Information -->
  <g id="UC_VIEW_SENTIMENT">
    <ellipse cx="590" cy="990" rx="165" ry="32" class="uc-oval" />
    <text x="590" y="987" class="usecase-text">View Sentiment &amp; Language Info</text>
    <text x="590" y="1004" class="usecase-sub">(BERT tone analysis &amp; language tag)</text>
  </g>


  <!-- Package 3: Central AI Generation -->
  <!-- Central UC: Generate AI-Assisted Response -->
  <g id="UC_GEN_AI">
    <ellipse cx="1060" cy="340" rx="190" ry="42" class="uc-oval" stroke-width="2.5" />
    <text x="1060" y="336" font-size="15px" font-weight="bold" fill="#000000" text-anchor="middle">Generate AI-Assisted Response</text>
    <text x="1060" y="355" class="usecase-sub">(Central AI &amp; RAG Orchestration)</text>
  </g>

  <!-- UC: Automatically Dispatch AI Response (Auto AI Mode) -->
  <g id="UC_AUTO_DISPATCH">
    <ellipse cx="1060" cy="530" rx="175" ry="36" class="uc-oval" />
    <text x="1060" y="527" class="usecase-text">Automatically Dispatch AI Response</text>
    <text x="1060" y="544" class="usecase-sub">(Auto AI Mode bypass for instant reply)</text>
  </g>


  <!-- Package 4: Human-in-the-Loop Review & Decisions -->
  <!-- UC: Review AI Draft -->
  <g id="UC_REVIEW_AI">
    <ellipse cx="1060" cy="770" rx="175" ry="35" class="uc-oval" />
    <text x="1060" y="767" class="usecase-text">Review AI Draft</text>
    <text x="1060" y="784" class="usecase-sub">(inspect suggestion in AI Suggestion Box)</text>
  </g>

  <!-- Decision 1: Accept AI Draft -->
  <g id="UC_ACCEPT_AI">
    <ellipse cx="940" cy="900" rx="100" ry="30" class="uc-oval" />
    <text x="940" y="898" class="usecase-text">Accept AI Draft</text>
    <text x="940" y="913" class="usecase-sub">(ready for dispatch)</text>
  </g>

  <!-- Decision 2: Edit AI Draft -->
  <g id="UC_EDIT_AI">
    <ellipse cx="1060" cy="990" rx="100" ry="30" class="uc-oval" />
    <text x="1060" y="988" class="usecase-text">Edit AI Draft</text>
    <text x="1060" y="1003" class="usecase-sub">(refine in composer)</text>
  </g>

  <!-- Decision 3: Reject AI Draft -->
  <g id="UC_REJECT_AI">
    <ellipse cx="1180" cy="900" rx="100" ry="30" class="uc-oval" />
    <text x="1180" y="898" class="usecase-text">Reject AI Draft</text>
    <text x="1180" y="913" class="usecase-sub">(dismiss suggestion)</text>
  </g>

  <!-- UC: Human Fallback / Manual Response -->
  <g id="UC_HUMAN_FALLBACK">
    <ellipse cx="950" cy="1130" rx="115" ry="32" class="uc-oval" />
    <text x="950" y="1127" class="usecase-text">Human Fallback</text>
    <text x="950" y="1143" class="usecase-sub">(manual override / compose)</text>
  </g>

  <!-- UC: Send Approved Response -->
  <g id="UC_SEND_APPROVED">
    <ellipse cx="1160" cy="1130" rx="125" ry="34" class="uc-oval" />
    <text x="1160" y="1127" class="usecase-text">Send Approved Response</text>
    <text x="1160" y="1144" class="usecase-sub">(human authorized send)</text>
  </g>


  <!-- Package 5: Channel Ingestion & Dispatch -->
  <!-- UC: Deliver Incoming Message -->
  <g id="UC_DELIVER_IN">
    <ellipse cx="1520" cy="340" rx="160" ry="36" class="uc-oval" />
    <text x="1520" y="337" class="usecase-text">Deliver Incoming Message</text>
    <text x="1520" y="354" class="usecase-sub">(inbound webhook &amp; sentiment parse)</text>
  </g>

  <!-- UC: Deliver Outgoing Response -->
  <g id="UC_DELIVER_OUT">
    <ellipse cx="1520" cy="850" rx="160" ry="36" class="uc-oval" />
    <text x="1520" y="847" class="usecase-text">Deliver Outgoing Response</text>
    <text x="1520" y="864" class="usecase-sub">(channel API / SMTP transmission)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- EXTERNAL USE CASES (Outside boundary) -->
  <!-- ================================================================================== -->
  <g id="UC_SEND_MSG">
    <ellipse cx="1940" cy="340" rx="145" ry="34" class="uc-oval" />
    <text x="1940" y="337" class="usecase-text">Send Customer Message</text>
    <text x="1940" y="353" class="usecase-sub">(via messaging channel)</text>
  </g>

  <g id="UC_RECV_RESP">
    <ellipse cx="1940" cy="850" rx="145" ry="34" class="uc-oval" />
    <text x="1940" y="847" class="usecase-text">Receive Business Reply</text>
    <text x="1940" y="863" class="usecase-sub">(in native client thread)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- ACTORS (Left: Internal Support Users, Right: External Entities) -->
  <!-- ================================================================================== -->

  <!-- Actor 1: Support User (Generalized Abstract Actor) -->
  <g id="ACTOR_SUPPORT_USER" transform="translate(180, 770)">
    <!-- Stick Figure -->
    <circle cx="0" cy="-35" r="16" fill="#ffffff" stroke="#000000" stroke-width="2" />
    <line x1="0" y1="-19" x2="0" y2="25" stroke="#000000" stroke-width="2.2" />
    <line x1="-28" y1="-5" x2="28" y2="-5" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="-22" y2="65" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="22" y2="65" stroke="#000000" stroke-width="2.2" />
    <text x="0" y="90" class="actor-label">Support User</text>
    <text x="0" y="108" class="actor-sub">&lt;&lt;actor&gt;&gt; Generalized</text>
  </g>

  <!-- Actor 2: Support Staff (Specialization 1) -->
  <g id="ACTOR_STAFF" transform="translate(80, 480)">
    <circle cx="0" cy="-28" r="13" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
    <line x1="0" y1="-15" x2="0" y2="20" stroke="#000000" stroke-width="1.8" />
    <line x1="-22" y1="-4" x2="22" y2="-4" stroke="#000000" stroke-width="1.8" />
    <line x1="0" y1="20" x2="-18" y2="52" stroke="#000000" stroke-width="1.8" />
    <line x1="0" y1="20" x2="18" y2="52" stroke="#000000" stroke-width="1.8" />
    <text x="0" y="74" class="actor-label" font-size="13px">Support Staff</text>
    <text x="0" y="90" class="actor-sub">Agent</text>
  </g>

  <!-- Actor 3: Business Admin (Specialization 2) -->
  <g id="ACTOR_ADMIN" transform="translate(80, 1050)">
    <circle cx="0" cy="-28" r="13" fill="#ffffff" stroke="#000000" stroke-width="1.8" />
    <line x1="0" y1="-15" x2="0" y2="20" stroke="#000000" stroke-width="1.8" />
    <line x1="-22" y1="-4" x2="22" y2="-4" stroke="#000000" stroke-width="1.8" />
    <line x1="0" y1="20" x2="-18" y2="52" stroke="#000000" stroke-width="1.8" />
    <line x1="0" y1="20" x2="18" y2="52" stroke="#000000" stroke-width="1.8" />
    <text x="0" y="74" class="actor-label" font-size="13px">Business Admin</text>
    <text x="0" y="90" class="actor-sub">Manager / Admin</text>
  </g>

  <!-- Actor Generalization Lines -->
  <!-- Support Staff -> Support User -->
  <path d="M 80 575 L 140 700" class="gen-line" />
  <!-- Business Admin -> Support User -->
  <path d="M 80 970 L 140 840" class="gen-line" />

  <!-- Actor 4: Customer / End User (External, Far Right) -->
  <g id="ACTOR_CUSTOMER" transform="translate(2020, 595)">
    <circle cx="0" cy="-35" r="16" fill="#ffffff" stroke="#000000" stroke-width="2" />
    <line x1="0" y1="-19" x2="0" y2="25" stroke="#000000" stroke-width="2.2" />
    <line x1="-28" y1="-5" x2="28" y2="-5" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="-22" y2="65" stroke="#000000" stroke-width="2.2" />
    <line x1="0" y1="25" x2="22" y2="65" stroke="#000000" stroke-width="2.2" />
    <text x="0" y="90" class="actor-label">Customer / End User</text>
    <text x="0" y="108" class="actor-sub">&lt;&lt;external actor&gt;&gt;</text>
  </g>

  <!-- Actor 5: Communication Platform (External System) -->
  <g id="ACTOR_PLATFORM" transform="translate(1520, 1170)">
    <rect x="-110" y="-35" width="220" height="70" rx="8" fill="#ffffff" stroke="#000000" stroke-width="2" />
    <text x="0" y="-12" class="actor-sub">&lt;&lt;external service&gt;&gt;</text>
    <text x="0" y="10" class="actor-label">Communication Platform</text>
    <text x="0" y="26" font-size="11" fill="#555555" text-anchor="middle">(Meta, WhatsApp, Email)</text>
  </g>


  <!-- ================================================================================== -->
  <!-- ASSOCIATIONS (Actor to Use Case lines) -->
  <!-- ================================================================================== -->

  <!-- Support User Associations -->
  <line x1="215" y1="760" x2="885" y2="770" class="assoc-line" /> <!-- to Review AI Draft -->
  <line x1="215" y1="780" x2="840" y2="900" class="assoc-line" /> <!-- to Accept AI Draft -->
  <line x1="215" y1="790" x2="960" y2="990" class="assoc-line" /> <!-- to Edit AI Draft -->
  <line x1="215" y1="800" x2="1080" y2="900" class="assoc-line" /> <!-- to Reject AI Draft -->
  <line x1="215" y1="810" x2="835" y2="1130" class="assoc-line" /> <!-- to Human Fallback -->
  <line x1="215" y1="820" x2="1035" y2="1130" class="assoc-line" /> <!-- to Send Approved Response -->

  <!-- Business Admin Specific Association -->
  <line x1="110" y1="1020" x2="435" y2="615" class="assoc-line" /> <!-- to Test Knowledge Retrieval -->

  <!-- Customer Associations -->
  <line x1="1980" y1="550" x2="1940" y2="375" class="assoc-line" /> <!-- Customer -> Send Message -->
  <line x1="1980" y1="640" x2="1940" y2="815" class="assoc-line" /> <!-- Customer -> Receive Response -->

  <!-- Communication Platform Associations -->
  <line x1="1520" y1="1135" x2="1520" y2="376" class="assoc-line" /> <!-- Platform -> Deliver Incoming -->
  <line x1="1520" y1="1135" x2="1520" y2="886" class="assoc-line" /> <!-- Platform -> Deliver Outgoing -->


  <!-- ================================================================================== -->
  <!-- UML INCLUDE & EXTEND RELATIONSHIPS -->
  <!-- ================================================================================== -->

  <!-- Inbound Ingestion Trigger -->
  <!-- Send Customer Message <<include>> Deliver Incoming Message -->
  <line x1="1795" y1="340" x2="1680" y2="340" class="dep-line" />
  <rect x="1705" y="323" width="70" height="18" fill="#ffffff" />
  <text x="1740" y="336" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Deliver Incoming Message <<include>> Generate AI-Assisted Response (Trigger) -->
  <line x1="1360" y1="340" x2="1250" y2="340" class="dep-line" />
  <rect x="1275" y="323" width="70" height="18" fill="#ffffff" />
  <text x="1310" y="336" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Central AI Generation Includes -->
  <!-- Generate AI Response <<include>> Retrieve Relevant Business Knowledge -->
  <path d="M 885 315 Q 820 270 755 270" class="dep-line" />
  <rect x="785" y="278" width="70" height="18" fill="#ffffff" />
  <text x="820" y="291" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Generate AI Response <<include>> Use Conversation Context -->
  <path d="M 870 340 L 755 390" class="dep-line" />
  <rect x="780" y="352" width="70" height="18" fill="#ffffff" />
  <text x="815" y="365" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Generate AI Response <<include>> Generate AI Response Draft -->
  <path d="M 885 365 Q 820 510 755 510" class="dep-line" />
  <rect x="785" y="445" width="70" height="18" fill="#ffffff" />
  <text x="820" y="458" class="rel-text">&lt;&lt;include&gt;&gt;</text>


  <!-- Explainability & Inspection Extends -->
  <!-- Display Sources <<extend>> Review AI Draft -->
  <path d="M 750 770 L 885 770" class="dep-line" />
  <rect x="785" y="753" width="66" height="16" fill="#ffffff" />
  <text x="818" y="765" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- Display Confidence <<extend>> Review AI Draft -->
  <path d="M 755 870 Q 820 830 885 790" class="dep-line" />
  <rect x="785" y="818" width="66" height="16" fill="#ffffff" />
  <text x="818" y="830" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- View Sentiment & Language <<extend>> Review AI Draft -->
  <path d="M 755 975 Q 830 900 900 800" class="dep-line" />
  <rect x="795" y="878" width="66" height="16" fill="#ffffff" />
  <text x="828" y="890" class="rel-text">&lt;&lt;extend&gt;&gt;</text>


  <!-- Human-in-the-Loop Review Extension from Generation -->
  <!-- Review AI Draft <<extend>> Generate AI-Assisted Response [Review Mode] -->
  <line x1="1060" y1="735" x2="1060" y2="382" class="dep-line" />
  <rect x="990" y="555" width="140" height="28" fill="#ffffff" stroke="#888888" stroke-width="0.8" rx="4" />
  <text x="1060" y="568" class="rel-text">&lt;&lt;extend&gt;&gt;</text>
  <text x="1060" y="580" class="condition-text">[Review Mode active]</text>

  <!-- Review AI Draft to Human Decision Specializations / Inclusions -->
  <!-- Accept AI Draft <<extend>> Review AI Draft -->
  <path d="M 975 872 L 1030 803" class="dep-line" />
  <rect x="970" y="830" width="66" height="16" fill="#ffffff" />
  <text x="1003" y="842" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- Edit AI Draft <<extend>> Review AI Draft -->
  <line x1="1060" y1="960" x2="1060" y2="805" class="dep-line" />
  <rect x="1027" y="875" width="66" height="16" fill="#ffffff" />
  <text x="1060" y="887" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- Reject AI Draft <<extend>> Review AI Draft -->
  <path d="M 1145 872 L 1090 803" class="dep-line" />
  <rect x="1085" y="830" width="66" height="16" fill="#ffffff" />
  <text x="1118" y="842" class="rel-text">&lt;&lt;extend&gt;&gt;</text>


  <!-- Decision to Dispatch / Fallback Flows -->
  <!-- Accept AI Draft <<include>> Send Approved Response -->
  <path d="M 990 928 L 1100 1100" class="dep-line" />
  <rect x="1015" y="1005" width="70" height="18" fill="#ffffff" />
  <text x="1050" y="1018" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Edit AI Draft <<include>> Send Approved Response -->
  <path d="M 1090 1018 L 1130 1096" class="dep-line" />
  <rect x="1075" y="1048" width="70" height="18" fill="#ffffff" />
  <text x="1110" y="1061" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Reject AI Draft <<extend>> Human Fallback -->
  <path d="M 1130 928 Q 1040 1020 985 1100" class="dep-line" />
  <rect x="1020" y="960" width="66" height="16" fill="#ffffff" />
  <text x="1053" y="972" class="rel-text">&lt;&lt;extend&gt;&gt;</text>

  <!-- Human Fallback <<extend>> Send Approved Response -->
  <line x1="1065" y1="1130" x2="1035" y2="1130" class="dep-line" />
  <rect x="1030" y="1120" width="66" height="16" fill="#ffffff" />
  <text x="1063" y="1132" class="rel-text">&lt;&lt;extend&gt;&gt;</text>


  <!-- Auto AI Mode Bypass Flow -->
  <!-- Automatically Dispatch <<extend>> Generate AI [Auto Mode] -->
  <line x1="1060" y1="494" x2="1060" y2="382" class="dep-line" />
  <rect x="990" y="425" width="140" height="28" fill="#ffffff" stroke="#888888" stroke-width="0.8" rx="4" />
  <text x="1060" y="438" class="rel-text">&lt;&lt;extend&gt;&gt;</text>
  <text x="1060" y="450" class="condition-text">[Auto AI Mode active]</text>

  <!-- Automatically Dispatch <<include>> Deliver Outgoing Response -->
  <path d="M 1235 530 Q 1400 530 1480 815" class="dep-line" />
  <rect x="1320" y="660" width="70" height="18" fill="#ffffff" />
  <text x="1355" y="673" class="rel-text">&lt;&lt;include&gt;&gt;</text>


  <!-- Outbound Delivery Flow -->
  <!-- Send Approved Response <<include>> Deliver Outgoing Response -->
  <line x1="1285" y1="1130" x2="1450" y2="880" class="dep-line" />
  <rect x="1340" y="990" width="70" height="18" fill="#ffffff" />
  <text x="1375" y="1003" class="rel-text">&lt;&lt;include&gt;&gt;</text>

  <!-- Deliver Outgoing Response <<include>> Receive Business Reply -->
  <line x1="1680" y1="850" x2="1795" y2="850" class="dep-line" />
  <rect x="1705" y="833" width="70" height="18" fill="#ffffff" />
  <text x="1740" y="846" class="rel-text">&lt;&lt;include&gt;&gt;</text>


  <!-- ================================================================================== -->
  <!-- WORKFLOW HIGHLIGHT NOTE: HUMAN-IN-THE-LOOP CORE PRINCIPLE -->
  <!-- ================================================================================== -->
  <g transform="translate(860, 1180)">
    <rect x="0" y="0" width="820" height="95" class="legend-box" />
    <text x="25" y="24" font-size="13" font-weight="bold" fill="#000000">Central Architecture Principle: Human-in-the-Loop RAG Governance</text>
    <text x="25" y="46" font-size="12" fill="#222222">
      • <tspan font-weight="bold">AI Assistance:</tspan> Contextually retrieves tenant knowledge chunks &amp; synthesizes suggested draft reply with source citations.
    </text>
    <text x="25" y="66" font-size="12" fill="#222222">
      • <tspan font-weight="bold">Human Oversight (Default):</tspan> Support Staff/Admin inspects draft, match percentage, and sentiment before deciding: <tspan font-weight="bold">Accept</tspan>, <tspan font-weight="bold">Edit</tspan>, or <tspan font-weight="bold">Reject</tspan>.
    </text>
    <text x="25" y="84" font-size="11.5" fill="#555555" font-style="italic">
      • <tspan font-weight="bold">Outbound Gatekeeper:</tspan> Only human-approved or human-fallback responses reach the customer (unless Auto AI Mode is explicitly set).
    </text>
  </g>

  <!-- ================================================================================== -->
  <!-- UML NOTATION LEGEND -->
  <!-- ================================================================================== -->
  <g transform="translate(385, 1285)">
    <text x="0" y="0" font-size="11" font-weight="bold" fill="#444444">UML 2.5 Notation:  —— Association   - - - &gt; &lt;&lt;include&gt;&gt; / &lt;&lt;extend&gt;&gt; Dependency   ———▷ Generalization   ( ) Use Case</text>
  </g>

</svg>
"""

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
diagram_dir = os.path.join(project_root, "docs", "diagrams", "use-case")
os.makedirs(diagram_dir, exist_ok=True)
svg_path = os.path.join(diagram_dir, "haqdesk_ai_rag_use_case.svg")
png_path = os.path.join(diagram_dir, "haqdesk_ai_rag_use_case.png")

with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg_code)

print(f"Saved SVG to {svg_path}")

doc = fitz.open(svg_path)
pix = doc[0].get_pixmap(dpi=300)
pix.save(png_path)
print(f"Rendered High-Res PNG to {png_path} ({pix.width}x{pix.height}px)")
