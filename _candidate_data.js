const dighaCandidates = [
  {
    id:1, sno:10, winner:true, name:"Sanjiv Chaurasia", party:"BJP", tag:"tag-a",
    age:56, education:"Doctorate \u2014 Ph.D, Ranchi University (2006); MBA, Patna University (1996); M.Com, Patna University (1993)",
    eduLevel:6, terms:3,
    profession:"MLA salary; Assistant Professor, S.S. Memorial College Ranchi (on lien)",
    criminalCount:3, criminalNote:"3 cases declared, all shown as pending trial in the affidavit \u2014 none listed as convicted. They relate to alleged offences including unlawful assembly, rioting, wrongful restraint/confinement and criminal intimidation, from three separate FIRs filed in Patna between 2015 and 2020; one has a revision appeal pending.",
    assets:"\u20b922,48,28,000 (~22 Crore+)", liabilities:"Nil",
    assetHistory:"Declared assets in his last two affidavits: \u20b97.73 Crore+ (Bihar 2020), \u20b95.33 Crore+ (Bihar 2015).",
    manifesto: NDA_MANIFESTO, manifestoNote:null,
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=179",
    newsStatus:"researched",
    background:[
      {text:"Son of Ganga Prasad, a veteran BJP leader and former Governor of Sikkim and Meghalaya."},
      {text:"Has represented Digha since 2015 \u2014 2025 is his third consecutive term, all three as the BJP nominee, each time defeating a CPI(ML)L challenger."},
      {text:"Declared assets rose from about \u20b95.33 crore (2015 affidavit) to \u20b97.73 crore (2020) to \u20b922.48 crore (2025) across his three candidacies."},
      {text:"His own campaign website lists local development work funded through his MLA Area Development Fund \u2014 drinking-water handpumps in Gurdanibagh/Bhikhachak Chamartoli and road-paving in Ward 22B and Rukanpura. This is self-reported by the candidate on his own site, not independently verified.", flag:true, flagLabel:"Self-reported, unverified"}
    ],
    newsLinks:[
      {title:"Political buzz in Patna: Can Sushant Singh Rajput's cousin unseat BJP's Sanjeev Chaurasia in Digha?", domain:"The Week", url:"https://www.theweek.in/news/india/2025/10/14/political-buzz-in-patna-can-sushant-singh-rajput-s-cousin-unseat-bjp-s-sanjeev-chaurasia-in-digha.html"},
      {title:"Sanjiv Chaurasiya", domain:"Wikipedia", url:"https://en.wikipedia.org/wiki/Sanjiv_Chaurasiya"},
      {title:"Digha constituency results 2025", domain:"India TV News", url:"https://www.indiatvnews.com/bihar/news-bihar-news-digha-constituency-bihar-assembly-election-results-2025-live-updates-leading-trailing-candidates-sanjiv-chaurasia-and-divya-gautam-2025-11-14-1016764"}
    ]
  },
  {
    id:2, sno:1, winner:false, name:"Divya Gautam", party:"CPI(ML)(L)", tag:"tag-b",
    age:33, education:"Post Graduate \u2014 M.A. Women's Studies, TISS Hyderabad (2016); Masters, Journalism & Mass Comm, Nalanda Open University (2018)",
    eduLevel:5, terms:0,
    profession:"Visiting faculty, Patna College, Patna",
    criminalCount:1, criminalNote:"1 case declared as pending in the affidavit. We haven't added the specific charge details yet \u2014 see the source link for the full record.",
    assets:"\u20b992,26,869 (~92 Lakh+)", liabilities:"Nil", assetHistory:null,
    manifesto: MGB_MANIFESTO, manifestoNote:null,
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=180",
    newsStatus:"researched",
    background:[
      {text:"Maternal cousin of the late actor Sushant Singh Rajput, whose family was from the Rajeev Nagar area within Digha's limits \u2014 a connection ground reporters say she has deliberately avoided leveraging on the campaign trail."},
      {text:"Long active in student politics: contested the Patna University Students' Union election in 2012 with AISA (CPI-ML's student wing), narrowly losing to an ABVP candidate."},
      {text:"Sources disagree on one detail: Wikipedia and a Deccan Herald report say she cleared the BPSC exam and qualified as a Supply Inspector but chose not to join government service; a separate Indiablooms report says she did join the post before later resigning to focus on activism. This demo hasn't independently resolved which is accurate.", flag:true, flagLabel:"Sources disagree"},
      {text:"Worked as an assistant professor at Patna Women's College before contesting."}
    ],
    newsLinks:[
      {title:"In Digha, Divya Gautam shuns Sushant Singh Rajput link", domain:"Deccan Herald", url:"https://www.deccanherald.com/amp/story/elections%2Fbihar%2Fin-digha-divya-shuns-sushant-link-3786677"},
      {title:"Sushant Singh Rajput's cousin Divya Gautam to contest Bihar polls", domain:"Indiablooms", url:"https://www.indiablooms.com/phoenix/public/news/sushant-singh-rajputs-cousin-divya-gautam-to-contest-bihar-polls-as-cpiml-candidate-from-digha/details"},
      {title:"Divya Gautam, Sushant Singh Rajput's Cousin, Promises 'Real Change'", domain:"ETV Bharat", url:"https://www.etvbharat.com/en/state/bihar-assembly-polls-2025-divya-gautam-sushant-singh-rajputs-cousin-enters-politics-to-challenge-bjps-sanjeev-chaurasia-in-digha-enn25110200710"},
      {title:"Divya Gautam", domain:"Wikipedia", url:"https://en.wikipedia.org/wiki/Divya_Gautam"}
    ]
  },
  {
    id:3, sno:2, winner:false, name:"Indu Devi", party:"Bharatiya Momin Front", tag:"tag-c",
    age:28, education:"8th pass", eduLevel:1, terms:0, profession:"Not listed in this data pull",
    criminalCount:0, criminalNote:"No pending criminal cases declared.",
    assets:"\u20b94,08,683 (~4 Lakh+)", liabilities:"Nil", assetHistory:null,
    manifesto: [], manifestoNote:"No published manifesto found for this party in this election.",
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=26",
    newsStatus:"no-coverage", background:[], newsLinks:[]
  },
  {
    id:4, sno:3, winner:false, name:"Kusumlata Verma", party:"Independent", tag:"tag-ind",
    age:56, education:"Post Graduate (1992) + LLB (1995), Magadh University", eduLevel:5, terms:0,
    profession:"Social worker, LIC agent",
    criminalCount:0, criminalNote:"No pending criminal cases declared.",
    assets:"Not available in this data pull", liabilities:"Not available in this data pull", assetHistory:null,
    manifesto: [], manifestoNote:"Contesting as an independent \u2014 no party manifesto.",
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=1311",
    newsStatus:"no-coverage", background:[], newsLinks:[]
  },
  {
    id:5, sno:4, winner:false, name:"Prabhakar Kumar Singh", party:"BSP", tag:"tag-c",
    age:61, education:"Graduate \u2014 B.Sc, BS College, Magadh University (1984)", eduLevel:4, terms:0,
    profession:"Retired state government servant",
    criminalCount:0, criminalNote:"No pending criminal cases declared.",
    assets:"\u20b914,67,44,426 (~14 Crore+)", liabilities:"\u20b961,28,907 (~61 Lakh+)", assetHistory:null,
    manifesto: [], manifestoNote:"No published manifesto found for BSP in this election.",
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=182",
    newsStatus:"no-coverage", background:[], newsLinks:[]
  },
  {
    id:6, sno:5, winner:false, name:"Pranjal Singh", party:"The Plurals Party", tag:"tag-c",
    age:29, education:"Post Graduate", eduLevel:5, terms:0, profession:"Not listed in this data pull",
    criminalCount:0, criminalNote:"No pending criminal cases declared.",
    assets:"\u20b94,40,549 (~4 Lakh+)", liabilities:"Nil", assetHistory:null,
    manifesto: [], manifestoNote:"No published manifesto found for this party in this election.",
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=545",
    newsStatus:"no-coverage",
    background:[{text:"No individual coverage of Pranjal Singh turned up, but the party itself has a public record: The Plurals Party was founded in March 2020 by Pushpam Priya Choudhary, a London School of Economics alumna who declared herself a Chief Ministerial candidate; the party has never won a seat, and Choudhary herself polled fewer votes than NOTA in one of her two 2020 seats."}],
    newsLinks:[{title:"Bihar CM aspirant Pushpam Priya loses both seats, gets fewer votes than NOTA", domain:"Tribune India", url:"https://www.tribuneindia.com/news/nation/bihar-cm-aspirant-pushpam-priya-lost-both-seats-gets-less-votes-than-nota-169219"}]
  },
  {
    id:7, sno:6, winner:false, name:"Rajiv Kumar Singh", party:"Right to Recall Party", tag:"tag-c",
    age:54, education:"Graduate", eduLevel:4, terms:0, profession:"Not listed in this data pull",
    criminalCount:0, criminalNote:"No pending criminal cases declared.",
    assets:"Not available in this data pull", liabilities:"Not available in this data pull", assetHistory:null,
    manifesto: [], manifestoNote:"No published manifesto found for this party in this election.",
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=1319",
    newsStatus:"no-coverage", background:[], newsLinks:[]
  },
  {
    id:8, sno:7, winner:false, name:"Richa Sinha", party:"Vocal India Party", tag:"tag-c",
    age:41, education:"Post Graduate \u2014 M.Tech, NIT Jamshedpur (2011)", eduLevel:5, terms:0, profession:"Business",
    criminalCount:0, criminalNote:"No pending criminal cases declared.",
    assets:"\u20b966,45,400 (~66 Lakh+)", liabilities:"Nil", assetHistory:null,
    manifesto: [], manifestoNote:"No published manifesto found for this party in this election.",
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=1316",
    newsStatus:"no-coverage", background:[], newsLinks:[]
  },
  {
    id:9, sno:8, winner:false, name:"Ritesh Ranjan Singh", party:"Jan Suraaj Party", tag:"tag-c",
    age:52, education:"Graduate", eduLevel:4, terms:0, profession:"Not listed in this data pull",
    criminalCount:0, criminalNote:"No pending criminal cases declared.",
    assets:"\u20b935,78,53,346 (~35 Crore+)", liabilities:"\u20b940,33,603 (~40 Lakh+)", assetHistory:null,
    manifesto: JANSURAAJ_AGENDA, manifestoNote:null,
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=181",
    newsStatus:"researched",
    background:[
      {text:"Known locally as \u201cBittu Singh\u201d; contested Digha as a first-time candidate for Jan Suraaj Party, finishing third."},
      {text:"In July 2026, after the Digha loss, he left Jan Suraaj and joined the BJP \u2014 shortly before the Bankipur bypoll in which Jan Suraaj founder Prashant Kishor is himself a candidate. He publicly apologised for joining Jan Suraaj \u201cin the heat of the moment.\u201d"}
    ],
    newsLinks:[
      {title:"How Jan Suraaj's KC Sinha and Bittu Singh joining BJP redefines the Bankipur bypoll", domain:"India TV News", url:"https://www.indiatvnews.com/bihar/news-how-jan-suraaj-s-kc-sinha-and-bittu-singh-joining-bjp-redefines-the-bankipur-bypoll-for-prashant-kishor-2026-07-15-1048363"}
    ]
  },
  {
    id:10, sno:9, winner:false, name:"Sadhana Kumari", party:"Jagrook Janta Party", tag:"tag-c",
    age:46, education:"12th pass \u2014 Inter, Bihar Board (1994)", eduLevel:2, terms:0,
    profession:"Customer care centre",
    criminalCount:0, criminalNote:"No pending criminal cases declared.",
    assets:"Not available in this data pull", liabilities:"Not available in this data pull", assetHistory:null,
    manifesto: [], manifestoNote:"No published manifesto found for this party in this election.",
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=1313",
    newsStatus:"no-coverage",
    background:[{text:"Enrolled as a voter in the neighbouring Phulwari constituency, not Digha itself \u2014 permitted under nomination rules, but worth knowing when weighing how rooted a candidate is in the seat they're contesting."}],
    newsLinks:[]
  },
  {
    id:11, sno:11, winner:false, name:"Shwet Ranjan", party:"Independent", tag:"tag-ind",
    age:31, education:"Graduate Professional", eduLevel:4, terms:0, profession:"Not listed in this data pull",
    criminalCount:1, criminalNote:"1 case declared as pending in the affidavit. We haven't added the specific charge details yet \u2014 see the source link for the full record.",
    assets:"\u20b975,972 (~75 Thousand+)", liabilities:"Nil", assetHistory:null,
    manifesto: [], manifestoNote:"Contesting as an independent \u2014 no party manifesto.",
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=1314",
    newsStatus:"no-coverage", background:[], newsLinks:[]
  }
];
dighaCandidates.sort((a,b)=>a.sno-b.sno);

const bankipurCandidates = [
  {
    id:101, sno:1, winner:false, name:"Neeraj Kumar Sinha", party:"BJP", tag:"tag-a",
    age:32, education:"Graduate \u2014 B.A., Magadh University, Sakurabad, Jahanabad (2024)", eduLevel:5, terms:0,
    profession:"Social worker & businessman; BJP Yuva Morcha (youth wing) organisational worker",
    criminalCount:0, criminalNote:"No pending criminal cases declared in the affidavit.",
    assets:"Not available \u2014 Hindi-language reporting on his affidavit states he owns no house; full figures not captured", liabilities:"Not available", assetHistory:null,
    manifesto: [], manifestoNote:"No individual manifesto found; contesting as the NDA/BJP's chosen candidate for this by-election.",
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=2964",
    newsStatus:"researched",
    background:[
      {text:"The BJP's original candidate for this seat was Abhishek Kumar Sinha, known as \u201cBunty,\u201d who withdrew a day after filing his nomination citing family reasons; reporting also links the switch to concern that his parents' connections to the fodder scam could be used against him by opponents.", flag:true, flagLabel:"Candidate was swapped days before filing"},
      {text:"The party replaced him with Sinha, a longer-serving BJYM worker rather than a high-profile name."},
      {text:"Filed his nomination alongside CM Samrat Choudhary and other senior NDA leaders; was accompanied to a temple visit beforehand by sitting BJP MLAs Sanjay Gupta and Sanjiv Chaurasia \u2014 the same Sanjiv Chaurasia who won Digha in this same election cycle."},
      {text:"His own MyNeta affidavit (indexed after this candidate's news-cycle name became public) lists his legal name as \u201cNeeraj Kumar,\u201d without \u201cSinha\u201d \u2014 every news source used in this app's research calls him Neeraj Kumar Sinha. Both are shown here rather than silently picking one; the affidavit is the authoritative legal document, the fuller name is how he is publicly known and campaigning.", flag:true, flagLabel:"Affidavit name differs from news coverage"}
    ],
    newsLinks:[
      {title:"BJP fields Neeraj Kumar Sinha in Bankipur bypoll after candidate swap", domain:"India TV News", url:"https://www.indiatvnews.com/bihar/news-bjp-fields-neeraj-kumar-sinha-in-bankipur-assembly-bypoll-after-candidate-abhishek-sinha-pulls-out-of-race-2026-07-10-1047838"},
      {title:"BJP candidate Neeraj Sinha files nomination for Bankipur bypolls", domain:"The Hans India", url:"https://www.thehansindia.com/news/national/bihar-bjp-candidate-neeraj-sinha-files-nomination-for-bankipur-bypolls-1097103"},
      {title:"Bankipur Byelection: Prashant Kishor Challenges BJP Stronghold in Patna", domain:"Outlook India", url:"https://www.outlookindia.com/national/bankipur-byelection-prashant-kishor-challenges-bjp-stronghold-in-patna"}
    ]
  },
  {
    id:102, sno:2, winner:false, name:"Prashant Kishor", party:"Jan Suraaj Party", tag:"tag-c",
    age:47, education:"Post Graduate \u2014 MHA, ASCI Hyderabad in collaboration with Johns Hopkins University (2001\u201303); BBA, Lucknow University (1996\u201399); 12th, Patna Science College (1993); 10th, Govt. School, Buxar (1991)",
    eduLevel:5, terms:0,
    profession:"Political advisor & consultant; founder of IPAC",
    criminalCount:8, criminalNote:"8 cases declared as pending, per his affidavit and news reporting. Charges have not yet even been framed in any of them, and he has not been convicted in any \u2014 an earlier stage than several other candidates in this app whose charges have been framed. Cases are reported to relate to alleged rioting and obstructing public servants; he has filed petitions in the Patna High Court in some of them.",
    assets:"\u20b996,00,00,000+ (~96 Crore+, his own declaration)", liabilities:"Not available", assetHistory:null,
    manifesto: JANSURAAJ_AGENDA, manifestoNote:null,
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=2966",
    newsStatus:"researched",
    background:[
      {text:"Founder of IPAC (Indian Political Action Committee) and a political strategist who has advised numerous parties over more than a decade; this bypoll is his own political debut as a candidate."},
      {text:"His wife, Dr Jahnavi Das, is an MBBS doctor and senior advisor at Apollo Indraprastha Hospital, New Delhi, and declared even greater personal assets \u2014 about \u20b9101.93 crore. Combined, the couple's declared wealth exceeds \u20b9197 crore."},
      {text:"Has publicly alleged that Deputy CM Samrat Choudhary submitted a fake age certificate to escape trial in a 1995 case linked to seven deaths in Tarapur; Choudhary has filed a separate defamation suit against Kishor over an unrelated, unproven bribery allegation. Neither claim has been decided by a court as of this writing.", flag:true, flagLabel:"Unresolved allegations, both directions"},
      {text:"On filing his nomination he said the contest was about \u201cpeople with criminal records\u201d having to \u201cgive up their chair\u201d \u2014 a notable framing given his own 8 pending cases, worth weighing on its own terms rather than taking either side's framing at face value."}
    ],
    newsLinks:[
      {title:"Bankipur Byelection: Prashant Kishor Challenges BJP Stronghold in Patna", domain:"Outlook India", url:"https://www.outlookindia.com/national/bankipur-byelection-prashant-kishor-challenges-bjp-stronghold-in-patna"},
      {title:"How Rich Is Prashant Kishor? Poll Affidavit Reveals \u20b996 Cr Assets", domain:"Daily Jagran", url:"https://www.thedailyjagran.com/india/how-rich-is-prashant-kishor-jan-suraaj-chiefs-poll-affidavit-reveals-rs-96-cr-assets-but-his-wife-is-richer-10320547"},
      {title:"Prashant Kishor slapped with defamation suit by Bihar minister Ashok Choudhary", domain:"Deccan Herald", url:"https://www.deccanherald.com/india/bihar/prashant-kishor-slapped-with-defamation-suit-by-bihar-minister-ashok-choudhary-3569180"},
      {title:"Prashant Kishore And Neeraj Sinha File Nominations", domain:"Dynamite News", url:"https://www.dynamitenews.com/politics/bankipur-assembly-by-poll-prashant-kishore-neeraj-sinha-filed-nominations"}
    ]
  },
  {
    id:103, sno:3, winner:false, name:"Rekha Gupta", party:"RJD", tag:"tag-b",
    age:46, education:"Graduate \u2014 B.A., Ram Narayan Memorial College (Vinoba Bhave University), Hazaribagh (2000)", eduLevel:5, terms:0,
    profession:"Businesswoman",
    criminalCount:1, criminalNote:"1 case declared as pending in the affidavit. Specific charge detail wasn't pulled in this pass \u2014 see the source link for the full record.",
    assets:"Not available", liabilities:"Not available", assetHistory:null,
    manifesto: MGB_MANIFESTO, manifestoNote:null,
    sourceUrl:"https://www.myneta.info/Bihar2025/candidate.php?candidate_id=2954",
    newsStatus:"researched",
    background:[
      {text:"Named as the RJD (Mahagathbandhan) candidate for the Bankipur bypoll."},
      {text:"Her MyNeta affidavit, indexed after the initial news-cycle reporting on her candidacy, lists her legal name as \u201cRekha Kumari\u201d \u2014 every news source used in this app's research calls her Rekha Gupta. Both are shown here rather than silently picking one; the affidavit is the authoritative legal document.", flag:true, flagLabel:"Affidavit name differs from news coverage"}
    ],
    newsLinks:[
      {title:"BJP fields Neeraj Kumar Sinha in Bankipur bypoll (confirms RJD's Rekha Gupta)", domain:"India TV News", url:"https://www.indiatvnews.com/bihar/news-bjp-fields-neeraj-kumar-sinha-in-bankipur-assembly-bypoll-after-candidate-abhishek-sinha-pulls-out-of-race-2026-07-10-1047838"},
      {title:"Bihar: BJP fields Neeraj Kumar Sinha for Bankipur bypoll after Abhishek Bunty withdraws", domain:"Prokerala", url:"https://www.prokerala.com/news/articles/a1786392.html"}
    ]
  }
];

const datiaCandidates = [
  {
    id:201, sno:1, winner:false, name:"Ashutosh Tiwari", party:"BJP", tag:"tag-a",
    age:null, education:"Not available", eduLevel:null, terms:0,
    profession:"BJP party worker",
    criminalCount:null, criminalNote:"We don't have this candidate's criminal case count yet \u2014 the coverage we found was about his declared assets, not his criminal record.",
    assets:"\u20b91.79 Crore+ (his own declaration)", liabilities:"\u20b911.83 Lakh+ (bank loan)",
    assetHistory:"His wife, Kalpana Tiwari, separately declared about \u20b91.76 crore, including over \u20b91.31 crore in agricultural land.",
    manifesto: [], manifestoNote:"No individual manifesto found; contesting as the BJP's chosen candidate for this by-election.",
    sourceUrl:null,
    newsStatus:"researched",
    background:[
      {text:"The BJP passed over Narottam Mishra \u2014 the party's former Home Minister and its 2023 candidate for this very seat \u2014 in favour of Tiwari, a lower-profile party worker. Mishra's supporters reportedly protested the decision before he publicly backed Tiwari's campaign.", flag:true, flagLabel:"Passed over a senior leader for this seat"},
      {text:"Introduced himself on filing his nomination as \u201can ordinary worker\u201d chosen by the party, standing next to Mishra and Chief Minister Mohan Yadav."}
    ],
    newsLinks:[
      {title:"BJP candidate Ashutosh files papers for Datia bypoll", domain:"The Hans India", url:"https://www.thehansindia.com/news/national/bjp-candidate-ashutosh-files-papers-for-datia-bypoll-1097268"},
      {title:"Datia Bypoll: Narottam Back BJP Candidate Ashutosh Tiwari", domain:"Daily Pioneer", url:"https://dailypioneer.com/news/datia-bypoll-narottam-back-bjp-candidate-ashutosh-tiwari"},
      {title:"Ghanshyam Singh-Ashutosh Tiwari Net Worth (candidate affidavits)", domain:"Khabar Digital", url:"https://khabardigital.com/madhya-pradesh/datia-bypoll-ghanshyam-singh-vs-ashutosh-tiwari-net-worth-property"}
    ]
  },
  {
    id:202, sno:2, winner:false, name:"Ghanshyam Singh", party:"INC", tag:"tag-b",
    age:null, education:"Not available", eduLevel:null, terms:0,
    profession:"Head of the former Datia royal family (\u201cRaja Saheb\u201d); landholder and businessman",
    criminalCount:null, criminalNote:"We don't have this candidate's criminal case count yet.",
    assets:"\u20b920.08 Crore+ (his own declaration \u2014 agricultural and non-agricultural land, commercial property, 240g gold)", liabilities:"\u20b95.63 Lakh+ (bank loan)",
    assetHistory:"His wife separately declared about \u20b984.17 lakh in assets and 580g of gold.",
    manifesto: MGB_MANIFESTO, manifestoNote:null,
    sourceUrl:"https://www.myneta.info/MadhyaPradesh2023/candidate.php?candidate_id=420",
    newsStatus:"researched",
    background:[
      {text:"Head of Datia's former princely family, popularly known as \u201cRaja Saheb\u201d \u2014 a real title, not a nickname invented for this app, confirmed by Hindi-language reporting on his affidavit."},
      {text:"An opposing BJP leader publicly contrasted him with Tiwari as someone \u201cborn into privilege\u201d against a candidate who \u201cdedicated his life to public service\u201d \u2014 that's the BJP's framing of the contest, not a neutral description, included here as campaign context rather than fact.", flag:true, flagLabel:"Opponent's framing, not neutral fact"}
    ],
    newsLinks:[
      {title:"Datia Bypoll: BJP vs Congress Prestige Fight", domain:"New Kerala", url:"https://www.newkerala.com/news/a/datia-bypoll-emerges-as-prestige-battle-bjp-congress-773.htm"},
      {title:"Ghanshyam Singh-Ashutosh Tiwari Net Worth (candidate affidavits)", domain:"Khabar Digital", url:"https://khabardigital.com/madhya-pradesh/datia-bypoll-ghanshyam-singh-vs-ashutosh-tiwari-net-worth-property"}
    ]
  },
  {
    id:203, sno:3, winner:false, name:"Sanjana Singh Kinnar", party:"Bharatiya Gan Warta Party", tag:"tag-c",
    age:null, education:"Not available", eduLevel:null, terms:0,
    profession:"Not available",
    criminalCount:null, criminalNote:"Not researched in this pass \u2014 no individual MyNeta affidavit page located yet.",
    assets:"Not available", liabilities:"Not available", assetHistory:null,
    manifesto: [], manifestoNote:"No published manifesto found for this party.",
    sourceUrl:null,
    newsStatus:"researched",
    background:[{text:"A transgender candidate whose run has been reported as bringing a \u201cfresh social and political dimension\u201d to the race \u2014 not seen as a front-runner in a BJP-vs-Congress contest, but reported as drawing interest among younger and urban voters."}],
    newsLinks:[{title:"Datia bypoll turns prestige battle for BJP, Congress", domain:"The Hans India", url:"https://www.thehansindia.com/news/national/datia-bypoll-turns-prestige-battle-for-bjp-congress-1098983"}]
  }
];

const CONSTITUENCIES = {
  digha: { label:"Digha (Patna), Bihar 2025", candidates: dighaCandidates, status:"concluded", note:null,
    banner:"Real data \u2014 Digha (Patna), Bihar 2025 Assembly Election, all 11 candidates. A declared criminal case is a charge, not a conviction." },
  bankipur: { label:"Bankipur (Patna), Bihar bypoll", candidates: bankipurCandidates, status:"upcoming", note:"This election hasn't happened yet \u2014 voting is 30 Jul 2026, results 3 Aug 2026. All three candidates shown have sourced MyNeta affidavit data as of 25 Jul 2026 (23 candidates filed in total for this seat; these three are the ones with substantial news coverage). Two candidates' affidavit names differ from how they're identified in news coverage \u2014 flagged on each candidate's card rather than resolved.",
    banner:"Real data \u2014 Bankipur (Patna) bypoll, voting 30 Jul 2026. A declared criminal case is a charge, not a conviction." },
  datia: { label:"Datia, Madhya Pradesh bypoll", candidates: datiaCandidates, status:"upcoming", note:"Also voting 30 Jul 2026, results 3 Aug 2026 \u2014 the same day as Bankipur, in a different state entirely. This seat is vacant because the sitting MLA was disqualified after being convicted in a fraud case \u2014 worth noting since most declared cases you'll see elsewhere are still pending trial, not convictions.",
    banner:"Real data \u2014 Datia, Madhya Pradesh bypoll, voting 30 Jul 2026. A declared criminal case is a charge, not a conviction." }
};

