// AgriEdge Smart Farm — Dashboard / UI / Integration

let latestData = null;

// DOM
const el = {
  empty: document.getElementById("result-empty"),
  content: document.getElementById("result-content"),
  image: document.getElementById("result-image"),
  badge: document.getElementById("status-badge"),
  meterFill: document.getElementById("meter-fill"),
  crop: document.getElementById("result-crop"),
  prediction: document.getElementById("result-prediction"),
  confidence: document.getElementById("result-confidence"),
  recommendation: document.getElementById("result-recommendation"),
  temperature: document.getElementById("temperature-value"),
  soilMoisture: document.getElementById("soil-moisture-value"),
  humidity: document.getElementById("humidity-value"),
  language: document.getElementById("language-select")
};

// AI translations
const dynamicTranslations = {
  en: {
    Tomato: "Tomato",
    Healthy: "Healthy",
    "Early Blight": "Early Blight",
    "Late Blight": "Late Blight",
    "Disease Detected": "Disease Detected",
    Uncertain: "Uncertain",
    Error: "Error"
  },
  hi: {
    Tomato: "टमाटर",
    Healthy: "स्वस्थ",
    "Early Blight": "अर्ली ब्लाइट",
    "Late Blight": "लेट ब्लाइट",
    "Disease Detected": "रोग पाया गया",
    Uncertain: "अनिश्चित",
    Error: "त्रुटि"
  },
  or: {
    Tomato: "ଟମାଟୋ",
    Healthy: "ସୁସ୍ଥ",
    "Early Blight": "ଆର୍ଲି ବ୍ଲାଇଟ୍",
    "Late Blight": "ଲେଟ୍ ବ୍ଲାଇଟ୍",
    "Disease Detected": "ରୋଗ ଚିହ୍ନଟ ହୋଇଛି",
    Uncertain: "ଅନିଶ୍ଚିତ",
    Error: "ତ୍ରୁଟି"
  },
  bn: {
    Tomato: "টমেটো",
    Healthy: "সুস্থ",
    "Early Blight": "আর্লি ব্লাইট",
    "Late Blight": "লেট ব্লাইট",
    "Disease Detected": "রোগ শনাক্ত হয়েছে",
    Uncertain: "অনিশ্চিত",
    Error: "ত্রুটি"
  }
};

// Recommendations
const recommendationTranslations = {
  en: {
    irrigationRequired: m =>
      `💧 Irrigation required. Soil moisture is ${m}%. Consider irrigating the crop.`,
    moistureAdequate:
      "💧 Soil moisture is adequate. No immediate irrigation is required.",
    heatStress: t =>
      `🌡️ Heat stress warning. Temperature is ${t}°C. Increase irrigation frequency and avoid pesticide application during peak heat.`,
    lowHumidity:
      "💨 Low humidity detected. Monitor the crop for water stress.",
    uncertain:
      "⚠️ AI result is uncertain. Take another clear image of the leaf for better analysis.",
    healthy:
      "✅ No significant disease detected. Continue regular crop monitoring.",
    disease: d =>
      `🌿 Possible ${d}. Monitor affected leaves and consider appropriate crop protection.`
  },

  hi: {
    irrigationRequired: m =>
      `💧 सिंचाई आवश्यक है। मिट्टी की नमी ${m}% है। फसल में सिंचाई करने पर विचार करें।`,
    moistureAdequate:
      "💧 मिट्टी की नमी पर्याप्त है। अभी सिंचाई की आवश्यकता नहीं है।",
    heatStress: t =>
      `🌡️ गर्मी के तनाव की चेतावनी। तापमान ${t}°C है। सिंचाई की आवृत्ति बढ़ाएं और अत्यधिक गर्मी के समय कीटनाशक का प्रयोग न करें।`,
    lowHumidity:
      "💨 कम नमी का पता चला। फसल में पानी की कमी के संकेतों पर नजर रखें।",
    uncertain:
      "⚠️ AI परिणाम अनिश्चित है। बेहतर विश्लेषण के लिए पत्ती की एक और स्पष्ट तस्वीर लें।",
    healthy:
      "✅ कोई महत्वपूर्ण रोग नहीं पाया गया। फसल की नियमित निगरानी जारी रखें।",
    disease: d =>
      `🌿 संभावित ${d}। प्रभावित पत्तियों पर नजर रखें और उचित फसल सुरक्षा उपायों पर विचार करें।`
  },

  or: {
    irrigationRequired: m =>
      `💧 ଜଳସେଚନ ଆବଶ୍ୟକ। ମାଟିର ଆର୍ଦ୍ରତା ${m}% ଅଛି। ଫସଲରେ ଜଳସେଚନ କରିବାକୁ ବିଚାର କରନ୍ତୁ।`,
    moistureAdequate:
      "💧 ମାଟିର ଆର୍ଦ୍ରତା ପର୍ଯ୍ୟାପ୍ତ ଅଛି। ବର୍ତ୍ତମାନ ଜଳସେଚନର ଆବଶ୍ୟକତା ନାହିଁ।",
    heatStress: t =>
      `🌡️ ଅତ୍ୟଧିକ ଗରମର ସତର୍କତା। ତାପମାତ୍ରା ${t}°C ଅଛି। ଜଳସେଚନର ଆବୃତ୍ତି ବଢ଼ାନ୍ତୁ ଏବଂ ଅତ୍ୟଧିକ ଗରମ ସମୟରେ କୀଟନାଶକ ପ୍ରୟୋଗ କରନ୍ତୁ ନାହିଁ।`,
    lowHumidity:
      "💨 କମ୍ ଆର୍ଦ୍ରତା ଚିହ୍ନଟ ହୋଇଛି। ଫସଲରେ ଜଳ ଅଭାବର ଲକ୍ଷଣ ଉପରେ ନଜର ରଖନ୍ତୁ।",
    uncertain:
      "⚠️ AI ଫଳାଫଳ ଅନିଶ୍ଚିତ। ଭଲ ବିଶ୍ଳେଷଣ ପାଇଁ ପତ୍ରର ଆଉ ଏକ ସ୍ପଷ୍ଟ ଫଟୋ ନିଅନ୍ତୁ।",
    healthy:
      "✅ କୌଣସି ଗୁରୁତର ରୋଗ ଚିହ୍ନଟ ହୋଇନାହିଁ। ଫସଲର ନିୟମିତ ନିରୀକ୍ଷଣ ଜାରି ରଖନ୍ତୁ।",
    disease: d =>
      `🌿 ସମ୍ଭାବ୍ୟ ${d}। ପ୍ରଭାବିତ ପତ୍ରଗୁଡ଼ିକ ଉପରେ ନଜର ରଖନ୍ତୁ ଏବଂ ଉପଯୁକ୍ତ ଫସଲ ସୁରକ୍ଷା ପଦକ୍ଷେପ ନିଅନ୍ତୁ।`
  },

  bn: {
    irrigationRequired: m =>
      `💧 সেচ প্রয়োজন। মাটির আর্দ্রতা ${m}%। ফসলে সেচ দেওয়ার কথা বিবেচনা করুন।`,
    moistureAdequate:
      "💧 মাটির আর্দ্রতা পর্যাপ্ত। এই মুহূর্তে সেচের প্রয়োজন নেই।",
    heatStress: t =>
      `🌡️ অতিরিক্ত তাপের সতর্কতা। তাপমাত্রা ${t}°C। সেচের পরিমাণ বাড়ান এবং অতিরিক্ত গরমের সময় কীটনাশক প্রয়োগ করবেন না।`,
    lowHumidity:
      "💨 কম আর্দ্রতা শনাক্ত হয়েছে। ফসলে জলের অভাবের লক্ষণ পর্যবেক্ষণ করুন।",
    uncertain:
      "⚠️ AI ফলাফল অনিশ্চিত। আরও ভালো বিশ্লেষণের জন্য পাতার একটি পরিষ্কার ছবি তুলুন।",
    healthy:
      "✅ কোনো উল্লেখযোগ্য রোগ শনাক্ত হয়নি। ফসলের নিয়মিত পর্যবেক্ষণ চালিয়ে যান।",
    disease: d =>
      `🌿 সম্ভাব্য ${d}। আক্রান্ত পাতাগুলি পর্যবেক্ষণ করুন এবং উপযুক্ত ফসল সুরক্ষা ব্যবস্থা গ্রহণের কথা বিবেচনা করুন।`
  }
};

// Disease translations
const diseaseTranslations = {
  en: {
    "Early Blight": "Early Blight",
    "Late Blight": "Late Blight"
  },
  hi: {
    "Early Blight": "अर्ली ब्लाइट",
    "Late Blight": "लेट ब्लाइट"
  },
  or: {
    "Early Blight": "ଆର୍ଲି ବ୍ଲାଇଟ୍",
    "Late Blight": "ଲେଟ୍ ବ୍ଲାଇଟ୍"
  },
  bn: {
    "Early Blight": "আর্লি ব্লাইট",
    "Late Blight": "লেট ব্লাইট"
  }
};

// UI translations
const translations = {
  en: {
    title: "AgriEdge Smart Farm",
    subtitle: "AI-powered crop monitoring and farmer assistance",
    language: "Language",
    captureTitle: "Capture a Leaf",
    chooseImage: "📷 Choose or capture a leaf image",
    analyze: "Analyze Leaf",
    captureHint: "Take a clear photo of a tomato leaf for AI analysis.",
    environment: "Farm Environment",
    temperature: "Temperature",
    soilMoisture: "Soil Moisture",
    humidity: "Humidity",
    cropHealth: "Crop Health",
    waiting: "Waiting for the first capture...",
    confidence: "Confidence",
    crop: "Crop",
    prediction: "Disease",
    farmerAction: "Farmer Action",
    recommendation: "Recommendation",
    waitingRecommendation: "Waiting for crop analysis."
  },

  hi: {
    title: "एग्रीएज स्मार्ट फार्म",
    subtitle: "AI आधारित फसल निगरानी और किसान सहायता",
    language: "भाषा",
    captureTitle: "पत्ती की तस्वीर लें",
    chooseImage: "📷 पत्ती की तस्वीर चुनें या लें",
    analyze: "पत्ती का विश्लेषण करें",
    captureHint: "AI विश्लेषण के लिए टमाटर की पत्ती की स्पष्ट तस्वीर लें।",
    environment: "खेत का वातावरण",
    temperature: "तापमान",
    soilMoisture: "मिट्टी की नमी",
    humidity: "हवा की नमी",
    cropHealth: "फसल का स्वास्थ्य",
    waiting: "पहली तस्वीर का इंतज़ार है...",
    confidence: "विश्वास स्तर",
    crop: "फसल",
    prediction: "रोग",
    farmerAction: "किसान के लिए सुझाव",
    recommendation: "सुझाव",
    waitingRecommendation: "फसल विश्लेषण का इंतज़ार है।"
  },

  or: {
    title: "ଏଗ୍ରିଏଜ୍ ସ୍ମାର୍ଟ ଫାର୍ମ",
    subtitle: "AI ଆଧାରିତ ଫସଲ ନିରୀକ୍ଷଣ ଏବଂ କୃଷକ ସହାୟତା",
    language: "ଭାଷା",
    captureTitle: "ପତ୍ରର ଫଟୋ ନିଅନ୍ତୁ",
    chooseImage: "📷 ପତ୍ରର ଫଟୋ ବାଛନ୍ତୁ କିମ୍ବା ନିଅନ୍ତୁ",
    analyze: "ପତ୍ର ବିଶ୍ଳେଷଣ କରନ୍ତୁ",
    captureHint: "AI ବିଶ୍ଳେଷଣ ପାଇଁ ଟମାଟୋ ପତ୍ରର ଏକ ସ୍ପଷ୍ଟ ଫଟୋ ନିଅନ୍ତୁ।",
    environment: "ଖେତର ପରିବେଶ",
    temperature: "ତାପମାତ୍ରା",
    soilMoisture: "ମାଟିର ଆର୍ଦ୍ରତା",
    humidity: "ବାୟୁର ଆର୍ଦ୍ରତା",
    cropHealth: "ଫସଲର ସ୍ୱାସ୍ଥ୍ୟ",
    waiting: "ପ୍ରଥମ ଫଟୋ ପାଇଁ ଅପେକ୍ଷା କରାଯାଉଛି...",
    confidence: "ନିଶ୍ଚିତତା",
    crop: "ଫସଲ",
    prediction: "ରୋଗ",
    farmerAction: "କୃଷକଙ୍କ ପାଇଁ ପରାମର୍ଶ",
    recommendation: "ପରାମର୍ଶ",
    waitingRecommendation: "ଫସଲ ବିଶ୍ଳେଷଣ ପାଇଁ ଅପେକ୍ଷା କରାଯାଉଛି।"
  },

  bn: {
    title: "এগ্রিএজ স্মার্ট ফার্ম",
    subtitle: "AI-চালিত ফসল পর্যবেক্ষণ এবং কৃষক সহায়তা",
    language: "ভাষা",
    captureTitle: "পাতার ছবি তুলুন",
    chooseImage: "📷 পাতার ছবি নির্বাচন করুন বা তুলুন",
    analyze: "পাতা বিশ্লেষণ করুন",
    captureHint: "AI বিশ্লেষণের জন্য টমেটো পাতার একটি পরিষ্কার ছবি তুলুন।",
    environment: "খামারের পরিবেশ",
    temperature: "তাপমাত্রা",
    soilMoisture: "মাটির আর্দ্রতা",
    humidity: "বাতাসের আর্দ্রতা",
    cropHealth: "ফসলের স্বাস্থ্য",
    waiting: "প্রথম ছবির জন্য অপেক্ষা করা হচ্ছে...",
    confidence: "নির্ভরযোগ্যতা",
    crop: "ফসল",
    prediction: "রোগ",
    farmerAction: "কৃষকের জন্য পরামর্শ",
    recommendation: "পরামর্শ",
    waitingRecommendation: "ফসল বিশ্লেষণের জন্য অপেক্ষা করা হচ্ছে।"
  }
};

// Status styles
const STATUS_STYLES = {
  HEALTHY: { label: "Healthy", cls: "healthy" },
  DISEASE_DETECTED: { label: "Disease Detected", cls: "disease" },
  UNCERTAIN: { label: "Uncertain", cls: "uncertain" },
  ERROR: { label: "Error", cls: "error" }
};

// Translate static UI
function changeLanguage(language) {
  const selected = translations[language] || translations.en;

  document.querySelectorAll("[data-i18n]").forEach(element => {
    const key = element.getAttribute("data-i18n");

    if (selected[key]) {
      element.textContent = selected[key];
    }
  });

  document.documentElement.lang = language;
}

// Translate recommendations
function translateRecommendation(text, language) {
  if (!text) {
    return "--";
  }

  const t =
    recommendationTranslations[language] ||
    recommendationTranslations.en;

  if (text.includes("Irrigation required")) {
    const match = text.match(/Soil moisture is\s+([\d.]+)%/);
    return t.irrigationRequired(match ? match[1] : "--");
  }

  if (text.includes("Soil moisture is adequate")) {
    return t.moistureAdequate;
  }

  if (text.includes("Heat stress warning")) {
    const match = text.match(/Temperature is\s+([\d.]+)°C/);
    return t.heatStress(match ? match[1] : "--");
  }

  if (text.includes("Low humidity detected")) {
    return t.lowHumidity;
  }

  if (text.includes("AI result is uncertain")) {
    return t.uncertain;
  }

  if (text.includes("No significant disease detected")) {
    return t.healthy;
  }

  if (text.includes("Possible")) {
    const match = text.match(/Possible\s+(.+?)\./);
    const disease = match ? match[1].trim() : "";

    const translated =
      diseaseTranslations[language]?.[disease] ||
      diseaseTranslations.en[disease] ||
      disease;

    return t.disease(translated);
  }

  return text;
}

// Render result
function render(data) {
  latestData = data;

  if (!data.has_result) {
    el.empty.classList.remove("hidden");
    el.content.classList.add("hidden");
    return;
  }

  el.empty.classList.add("hidden");
  el.content.classList.remove("hidden");

  const language = el.language?.value || "en";

  const dynamic =
    dynamicTranslations[language] ||
    dynamicTranslations.en;

  if (data.image_url) {
    el.image.src = data.image_url;
  }

  const style =
    STATUS_STYLES[data.status] ||
    STATUS_STYLES.ERROR;

  el.badge.textContent =
    dynamic[style.label] || style.label;

  el.badge.className =
    `badge badge-${style.cls}`;

  const confidence =
    data.confidence != null
      ? Math.max(
          0,
          Math.min(100, Number(data.confidence) * 100)
        )
      : 0;

  el.meterFill.className =
    `meter-fill fill-${style.cls}`;

  el.meterFill.style.width =
    `${confidence}%`;

  el.confidence.textContent =
    data.confidence != null
      ? `${confidence.toFixed(1)}%`
      : "--";

  el.crop.textContent =
    dynamic[data.crop] ||
    data.crop ||
    "--";

  el.prediction.textContent =
    dynamic[data.prediction] ||
    data.prediction ||
    "--";

  if (data.temperature != null) {
    el.temperature.textContent = data.temperature;
  }

  if (data.soil_moisture != null) {
    el.soilMoisture.textContent = data.soil_moisture;
  }

  if (data.humidity != null) {
    el.humidity.textContent = data.humidity;
  }

  if (data.recommendation) {
    el.recommendation.textContent =
      translateRecommendation(
        data.recommendation,
        language
      );
  } else if (data.error) {
    el.recommendation.textContent = data.error;
  } else {
    el.recommendation.textContent = "--";
  }
}

// Refresh data
async function refresh() {
  try {
    const response = await fetch("/api/latest");

    if (!response.ok) {
      console.error("Server returned:", response.status);
      return;
    }

    const data = await response.json();
    render(data);
  } catch (error) {
    console.error("Could not refresh latest result:", error);
  }
}

// Language selector
if (el.language) {
  el.language.addEventListener("change", () => {
    changeLanguage(el.language.value);

    if (latestData) {
      render(latestData);
    }
  });
}

// Start
changeLanguage(el.language?.value || "en");
refresh();

setInterval(refresh, 4000);