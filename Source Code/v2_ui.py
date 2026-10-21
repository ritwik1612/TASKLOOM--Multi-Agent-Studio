"""Shared dark, square-edged Taskloom v2 presentation helpers."""

from __future__ import annotations


def star_svg() -> str:
    """A lightweight, scalable workflow illustration; no WebGL or video needed."""
    return '''<svg class="v2-star" viewBox="0 0 760 560" role="img" aria-label="Prompt flows through a host agent to specialists and review" preserveAspectRatio="xMidYMid meet">
      <defs><linearGradient id="v2-metal" x1="0" y1="0" x2="760" y2="560" gradientUnits="userSpaceOnUse"><stop stop-color="#e4edff"/><stop offset=".32" stop-color="#5d79b7"/><stop offset=".62" stop-color="#c8d8ff"/><stop offset="1" stop-color="#4e6aab"/></linearGradient></defs>
      <g fill="none" stroke="url(#v2-metal)" stroke-width="1.5" opacity=".75">
        <path id="v2-input" d="M75 280 C195 280 275 280 400 280"/>
        <path id="v2-plan" d="M400 280 C470 180 520 145 590 115"/>
        <path id="v2-worker-one" d="M400 280 C525 245 620 225 710 220"/>
        <path id="v2-worker-two" d="M400 280 C505 320 590 365 670 390"/>
        <path id="v2-return" d="M670 390 C555 360 460 320 400 280"/>
        <path id="v2-review" d="M400 280 C432 380 485 450 540 500"/>
      </g>
      <g class="v2-nodes" fill="#091935" stroke="#91aef8" stroke-width="1.7">
        <circle cx="75" cy="280" r="17"/><circle cx="590" cy="115" r="15"/><circle cx="710" cy="220" r="15"/><circle cx="670" cy="390" r="15"/><circle cx="540" cy="500" r="17"/>
      </g>
      <g fill="#adc3fa"><circle cx="75" cy="280" r="3"/><circle cx="590" cy="115" r="3"/><circle cx="710" cy="220" r="3"/><circle cx="670" cy="390" r="3"/><circle cx="540" cy="500" r="3"/></g>
      <g class="v2-hub" fill="none" stroke="#c2d3ff" stroke-linecap="butt"><path d="M394 239 L405 319" stroke-width="2.2"/><path d="M362 273 L445 286" stroke-width="2"/><path d="M370 311 L432 250" stroke-width="2.4"/></g>
      <circle class="v2-flow" r="3.2"><animateMotion dur="7s" repeatCount="indefinite" path="M75 280 C195 280 275 280 400 280 C525 245 620 225 710 220 C525 245 455 260 400 280 C432 380 485 450 540 500"/></circle>
      <g class="v2-labels" text-anchor="middle"><text x="75" y="321">PROMPT</text><text x="590" y="82">PLAN</text><text x="710" y="188">WORKER 01</text><text x="670" y="430">WORKER 02</text><text x="540" y="542">REVIEW</text><text x="400" y="359">HOST AGENT</text></g>
    </svg>'''


def styles(night_sky_uri: str, ribbon_uri: str) -> str:
    return '''<style>
      :root{--v2-bg:#020611;--v2-panel:#081328;--v2-line:rgba(180,201,245,.17);--v2-text:#f5f1e8;--v2-soft:#b8c2d8;--v2-cobalt:#3159df}
      html,body,[data-testid="stAppViewContainer"],.stApp{background:#020611!important;color:var(--v2-text)!important}
      .stApp{background:linear-gradient(180deg,rgba(1,4,13,.85),rgba(2,6,17,.94) 58%,#020611),url("__NIGHT_SKY__") center top/cover fixed!important}
      .stApp::before{background:radial-gradient(circle at 68% 33%,transparent,rgba(1,4,12,.8) 100%)!important}
      .block-container{max-width:1280px!important;padding-top:4.9rem!important}
      .maf-nav{display:none!important}
      .stApp,.stApp p,.stApp label,.stApp button,.stApp input,.stApp textarea,.stApp small{font-family:'Courier Prime','Courier New',monospace!important}
      .stApp h1,.stApp h2,.stApp h3,.maf-hero h1,.maf-chat-intro h1{font-family:'Taskloom Olivera',Georgia,serif!important;font-weight:400!important}
      .stApp h1,.stApp h2,.stApp h3{letter-spacing:-.05em!important}
      .maf-kicker,.maf-section-label,.maf-eyebrow{display:none!important}
      .maf-hero{display:grid!important;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr)!important;align-items:center!important;gap:1rem!important;min-height:430px!important;padding:1rem 0!important;background:transparent!important;overflow:visible!important}
      .maf-hero-copy{grid-column:1;grid-row:1;text-align:left!important;width:100%!important;max-width:none!important}
      .maf-hero h1,.maf-hero h1 span{font-family:'Taskloom Olivera',Georgia,serif!important;font-size:clamp(4.5rem,7vw,7.4rem)!important;line-height:.83!important;letter-spacing:-.06em!important;margin:0!important}
      .maf-hero h1{margin-bottom:2rem!important}.maf-hero h1 .maf-hero-primary{color:#f5f1e8!important}.maf-hero h1 .maf-hero-accent{color:#c4d1fa!important}
      .maf-hero p{max-width:470px!important;color:#c9d0df!important;font-size:1rem!important;line-height:1.72!important;margin:0!important}
      .maf-hero .v2-star{grid-column:2;grid-row:1;width:100%;max-width:670px;min-width:0;overflow:visible}
      .v2-star .v2-hub{filter:drop-shadow(0 0 5px #7195ee);animation:v2-pulse 3s ease-in-out infinite}.v2-star .v2-flow{fill:#e6eeff;filter:drop-shadow(0 0 6px #a4bcff)}
      .v2-star .v2-labels{fill:#adc1ef;font:700 12px 'Courier Prime','Courier New',monospace;letter-spacing:1.2px}
      @keyframes v2-pulse{50%{filter:drop-shadow(0 0 10px #92adff)}}
      .v2-diagram{max-width:780px;margin:1rem auto 2rem;padding:12px;border:1px solid var(--v2-line);background:#081328}.v2-diagram .v2-star{display:block;width:100%;height:auto;max-height:440px}
      .maf-panel-hero,.maf-chat-intro{background:transparent!important}.maf-panel-hero h1,.maf-chat-intro h1{color:#f5f1e8!important}
      .maf-panel-hero p,.maf-chat-intro p{color:#c9d0df!important}
      .maf-network,.maf-chat-network{display:none!important}
      [data-testid="stMetric"],.maf-info-card dl div,.maf-agent-card,.maf-map-detail,.maf-architecture-detail,.maf-architecture-flow>div,.maf-connect-step,.maf-connection-status>div,[data-testid="stExpander"],.maf-preview,.st-key-output_content{background:#081328!important;border:1px solid var(--v2-line)!important;box-shadow:none!important}
      .stApp .stButton>button,.stApp .stDownloadButton>button,.stApp [data-testid="stPopoverButton"],.stApp [data-testid="stMetric"],.stApp [data-testid="stExpander"],.stApp [data-testid="stTextArea"] textarea,.stApp [data-testid="stTextInput"] input{border-radius:0!important;clip-path:none!important}
      .stButton>button,.stDownloadButton>button,[data-testid="stPopoverButton"]{min-height:42px!important;transition:background .18s ease,border-color .18s ease!important}
      .stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:#3159df!important;border:1px solid #4167ef!important;color:#fff!important;box-shadow:none!important}
      .stButton>button[kind="primary"]:hover{background:#4169f0!important;transform:none!important}
      .stButton>button:not([kind="primary"]),.stDownloadButton>button,[data-testid="stPopoverButton"]{background:#091a39!important;border:1px solid #3655a2!important;color:#d7e2ff!important;box-shadow:none!important}
      .stButton>button:not([kind="primary"]):hover,.stDownloadButton>button:hover,[data-testid="stPopoverButton"]:hover{background:#142c60!important;transform:none!important;box-shadow:none!important}
      [data-testid="stTextArea"] textarea,[data-testid="stTextInput"] input{background:#081328!important;border:1px solid #4962a3!important;border-radius:0!important;color:#f5f1e8!important;box-shadow:none!important}
      [data-testid="stTabs"] [role="tablist"]{overflow-x:auto;scrollbar-width:thin}
      [data-testid="stTabs"] [role="tab"]{min-width:max-content!important}
      .maf-agent-card,.maf-map-detail,.maf-architecture-detail,.maf-architecture-flow>div,.maf-connect-step,.maf-connection-status>div,.maf-info-card dl div{border-radius:0!important}
      .maf-back-anchor+div .stButton>button{color:#cad8fb!important}
      .st-key-v2_sidebar{position:fixed!important;top:68px;left:0;bottom:0;z-index:10090;width:320px;max-width:100vw;overflow:auto;padding:26px 22px;background:#07152d;border-right:1px solid var(--v2-line);box-shadow:18px 0 50px #0008}
      .st-key-v2_sidebar h2{font-size:2.4rem!important;margin:.5rem 0 1.2rem}.st-key-v2_sidebar .stButton>button{justify-content:space-between!important;width:100%!important;background:transparent!important;border:0!important;border-top:1px solid var(--v2-line)!important;color:#d3def8!important;text-align:left!important;padding:.8rem .3rem!important}
      .st-key-v2_sidebar .stButton>button>div{width:100%!important;justify-content:flex-start!important}.st-key-v2_sidebar .stButton>button p{text-align:left!important}
      .st-key-v2_sidebar .stButton>button:hover{background:#172c59!important}
      div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"] .stButton>button{background-size:38px 44px!important;width:185px!important}
      div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"] .stButton>button::after{color:#f5f1e8!important;font-size:1.2rem!important}
      div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"] .stButton>button::before{display:none!important}
      div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor)+div[data-testid="stElementContainer"]{right:max(24px,calc((100vw - 1180px)/2))!important;width:164px!important}
      div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor)+div[data-testid="stElementContainer"] .stButton{width:164px!important;background:transparent!important;clip-path:none!important;box-shadow:none!important}
      div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor)+div[data-testid="stElementContainer"] .stButton>button{width:164px!important;background:#3159df!important;border:0!important;clip-path:none!important;box-shadow:4px 4px 0 #173b93!important}
      div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor)+div[data-testid="stElementContainer"] .stButton>button::after{color:#fff!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.66rem!important}
      .st-key-agent_menu_slot{display:none!important}
      div[data-testid="stElementContainer"]:has(.v2-home-anchor)+div[data-testid="stElementContainer"]{position:fixed!important;z-index:10080!important;top:16px!important;right:calc(max(24px,calc((100vw - 1180px)/2)) + 176px)!important;width:70px!important}
      div[data-testid="stElementContainer"]:has(.v2-home-anchor)+div[data-testid="stElementContainer"] .stButton>button{width:70px!important;min-height:36px!important;height:36px!important;padding:0!important;background:transparent!important;color:#dce5fa!important;font-size:.64rem!important}
      .v2-history-title{font-family:'Taskloom Olivera',Georgia,serif;font-size:clamp(2.5rem,5vw,4.5rem);line-height:1;margin:1rem 0}.v2-history-intro{color:#b8c2d8;max-width:650px}
      .v2-history-record{border-top:1px solid var(--v2-line);padding:1rem 0;color:#b8c2d8;font-size:.8rem}
      @media(max-width:700px){
        .block-container{padding:5.1rem 1rem 2rem!important;width:100%!important;max-width:100%!important;overflow-x:hidden!important}
        .maf-chat-intro{margin-top:.4rem!important;padding:1rem 0 1.4rem!important}
        .maf-panel-hero{margin:1rem 0!important;padding:1rem 0 1.5rem!important}
        .maf-hero{grid-template-columns:1fr!important;min-height:0!important;gap:0!important;padding:2rem 0 0!important}
        .maf-hero-copy{grid-column:1;grid-row:1}.maf-hero .v2-star{grid-column:1;grid-row:2;max-height:360px;margin-top:1rem}
        .maf-hero h1,.maf-hero h1 span{font-size:clamp(3rem,13vw,5rem)!important;line-height:.88!important}
        .maf-hero p{font-size:.9rem!important;line-height:1.6!important}
        .maf-hero+div{margin-top:0!important}
        .maf-panel-hero h1,.maf-chat-intro h1{font-size:clamp(2.7rem,11vw,4rem)!important;overflow-wrap:anywhere}
        .st-key-v2_sidebar{width:100vw;max-width:none;border-right:0;box-shadow:none;padding:25px 24px}
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"]{left:12px!important;top:8px!important;width:132px!important}
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"] .stButton>button{width:132px!important;background-size:32px 40px!important}
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"] .stButton>button::after{left:42px!important;top:14px!important;font-size:.94rem!important}
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor)+div[data-testid="stElementContainer"]{right:12px!important;top:15px!important;width:126px!important}
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor)+div[data-testid="stElementContainer"] .stButton{width:126px!important}
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor)+div[data-testid="stElementContainer"] .stButton>button{width:126px!important;min-height:32px!important;height:32px!important}
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor)+div[data-testid="stElementContainer"] .stButton>button::after{font-size:.53rem!important}
        div[data-testid="stElementContainer"]:has(.v2-home-anchor)+div[data-testid="stElementContainer"]{top:18px!important;right:148px!important;width:56px!important}
        div[data-testid="stElementContainer"]:has(.v2-home-anchor)+div[data-testid="stElementContainer"] .stButton>button{width:56px!important;height:29px!important;min-height:29px!important;font-size:.55rem!important}
        [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}
        [data-testid="column"]{min-width:min(100%,180px)!important;flex:1 1 180px!important}
        [data-testid="stMetric"]{min-width:0!important}
        .maf-agent-map,.maf-agent-branches,.maf-map-detail-grid,.maf-architecture-detail-grid,.maf-message-flow,.maf-connect-steps,.maf-connection-status{grid-template-columns:1fr!important}
        .maf-architecture-flow{flex-direction:column!important}
        .v2-diagram{padding:0}
      }
      @media(max-width:390px){.st-key-v2_sidebar{top:68px}.maf-hero h1,.maf-hero h1 span{font-size:13vw!important}}
      @media(prefers-reduced-motion:reduce){.v2-star .v2-hub{animation:none!important}.v2-star .v2-flow{display:none!important}}
      /* The silver-and-cobalt woven mark from the approved browser concept. */
      div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"] .stButton>button{
        background:transparent!important;filter:none!important;
      }
      div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"] .stButton>button::before{
        content:""!important;display:block!important;position:absolute!important;left:0!important;top:2px!important;
        width:39px!important;height:48px!important;background:linear-gradient(130deg,#3855a0 0%,#e6eeff 18%,#7f9fda 35%,#2445aa 53%,#d2def9 72%,#536caa 100%)!important;
        -webkit-mask:url("__RIBBON__") center/contain no-repeat!important;mask:url("__RIBBON__") center/contain no-repeat!important;
        filter:drop-shadow(0 1px 7px rgba(167,189,246,.35))!important;
      }
      div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"] .stButton>button::after{color:#f5f1e8!important}
      .taskloom-splash img{display:none!important}
      .taskloom-splash::after{content:"";display:block;position:relative;z-index:1;width:135px;height:155px;
        background:linear-gradient(130deg,#3855a0 0%,#e6eeff 18%,#7f9fda 35%,#2445aa 53%,#d2def9 72%,#536caa 100%);
        -webkit-mask:url("__RIBBON__") center/contain no-repeat;mask:url("__RIBBON__") center/contain no-repeat;
        filter:drop-shadow(0 0 20px rgba(133,159,232,.2));animation:taskloom-ribbon-arrive .95s .08s var(--maf-ease) both;
      }
      .taskloom-splash strong{color:#e6eeff!important}
      /* Shared chat/output workspace vocabulary: calm surfaces, square edges, flat cobalt actions. */
      .block-container>.stVerticalBlock{gap:0!important}
      .v3-page-intro{display:grid;grid-template-columns:1.2fr 1fr;column-gap:2rem;align-items:end;border-bottom:1px solid var(--v2-line);padding:.4rem 0 1.5rem;margin:1.5rem 0 1.4rem}
      .v3-page-intro>span,.v3-work-head,.v3-chat-intro small,.v3-aside small{font:700 .67rem 'Courier Prime','Courier New',monospace;letter-spacing:.12em;color:#9fb6f2}
      .v3-page-intro>span{grid-column:1;grid-row:1}
      .v3-page-intro>[data-testid="stHeadingWithActionElements"]{grid-column:1;grid-row:2}
      .v3-page-intro>p{grid-column:2;grid-row:1/span 2;align-self:end}
      .v3-page-intro h1{font:400 clamp(2.6rem,5vw,4.4rem)/.98 'Taskloom Olivera',Georgia,serif!important;margin:.8rem 0 0;letter-spacing:-.055em!important}
      .v3-page-intro p{color:#bdc8df;font-size:.88rem;line-height:1.7;margin:0;max-width:440px}
      .st-key-v3_chat_main,.st-key-v3_chat_aside{background:#080d1d;border:1px solid var(--v2-line);padding:1.7rem}
      .st-key-v3_chat_main .stButton>button:not([kind="primary"]){background:#0b1329!important;border-color:#273856!important}
      .st-key-v3_chat_main .stButton>button:hover,.st-key-v3_chat_aside .stButton>button:hover{background:#152758!important;border-color:#5778cd!important}
      .v3-work-head{display:flex;justify-content:space-between;gap:1rem;border-bottom:1px solid var(--v2-line);padding-bottom:1rem}
      .v3-work-head span:last-child{color:#9ca9c3}
      .v3-chat-intro{padding:2.2rem 0 1rem}
      .v3-chat-intro h2{font:400 clamp(2.2rem,4vw,3.6rem)/1 'Taskloom Olivera',Georgia,serif!important;margin:.8rem 0!important}
      .v3-chat-intro p,.v3-aside p{color:#bdc8df;font-size:.82rem;line-height:1.8}
      .v3-chat-intro p{max-width:640px}
      .st-key-v3_chat_main [data-testid="stTextArea"] textarea{min-height:164px!important;border-color:#304474!important}
      .st-key-v3_chat_main [data-testid="stCaptionContainer"]{color:#8998bb!important;font-size:.7rem!important}
      .v3-aside h3{font:400 2rem/1.07 'Taskloom Olivera',Georgia,serif!important;margin:1.5rem 0!important}
      .v3-aside p{border-top:1px solid var(--v2-line);padding-top:1.2rem;line-height:2.4}
      .maf-workspace-head{border-bottom:1px solid var(--v2-line)!important;padding:0 0 1.35rem!important;margin:1.4rem 0!important}
      .maf-workspace-head h2{font:400 clamp(2.5rem,5vw,4.2rem)/1 'Taskloom Olivera',Georgia,serif!important}
      [data-testid="stMetric"]{background:#080d1d!important;min-height:104px;padding:.9rem 1rem!important}
      [data-testid="stTabs"] [role="tablist"]{border:1px solid var(--v2-line);background:#080d1d;padding:.3rem!important;gap:.25rem!important}
      [data-testid="stTabs"] [role="tab"]{padding:.7rem 1rem!important;border:0!important;color:#c2cce0!important}
      [data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:#f1eee5!important;color:#0b1222!important}
      [data-testid="stTabs"] [role="tab"][aria-selected="true"] *{color:#0b1222!important}
      .maf-role{clip-path:none!important;background:#3159df!important}
      .st-key-output_content{padding:1.5rem!important;background:#080d1d!important}
      .maf-usage-limit{border-radius:0!important;background:#151515!important;border:1px solid #a59475!important;box-shadow:none!important}
      .maf-usage-limit h3{color:#f5f1e8!important}.maf-usage-limit p{color:#d0c9bf!important}
      .maf-usage-limit-mark{border-radius:0!important;background:#3159df!important;color:#fff!important}
      .v3-error-code{font:700 .66rem 'Courier Prime','Courier New',monospace;letter-spacing:.1em;color:#e5c898;margin-bottom:.6rem}
      @media(max-width:850px){.v3-page-intro{grid-template-columns:1fr;gap:.5rem}.v3-page-intro>p{grid-column:1;grid-row:3}.st-key-v3_chat_main,.st-key-v3_chat_aside{padding:1.2rem}}
      @media(max-width:700px){div[data-testid="stElementContainer"]:has(.maf-home-native-anchor)+div[data-testid="stElementContainer"] .stButton>button::before{width:32px!important;height:40px!important}}
      *,*::before,*::after{border-radius:0!important}
    </style>'''.replace("__NIGHT_SKY__", night_sky_uri).replace("__RIBBON__", ribbon_uri)
