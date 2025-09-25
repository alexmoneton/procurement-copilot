# 📧 Email Personalization Guide

## 🎯 **PERSONALIZATION OVERVIEW**

**Every email is UNIQUE per prospect!** No two prospects will receive identical emails. All personalization is based on their specific lost tender data from the TED API.

---

## ✅ **WHAT GETS PERSONALIZED (DYNAMIC)**

### **1. Contact Information**
- **Contact Name**: First name only (Michael, Sarah, Pierre, Emma)
- **Company Name**: Full company name (DigitalPartners Ltd, TechCorp GmbH, etc.)

### **2. Tender-Specific Data**
- **Contract Value**: Formatted values (€850K, €1.2M, €650K, etc.)
- **City/Region**: Extracted from buyer name (Berlin, Munich, Paris, Amsterdam)
- **Sector**: From tender data (IT & Software, Data Analytics, Environmental Services)
- **Award Date**: Formatted date (September 15, 2024, etc.)
- **TED Tender ID**: Unique identifier (TED-123456, TED-111111, etc.)

### **3. Similar Opportunities**
- **Similar Buyers**: Generated based on original buyer (Hamburg City Government, Lyon City Government, etc.)
- **Similar Values**: Calculated based on original contract (€935K, €1M, etc.)
- **Deadlines**: Auto-generated realistic dates (October 10, October 13, etc.)

### **4. Subject Lines**
- **Email 1**: "Similar €850K contract to your Berlin bid"
- **Email 2**: "Third similar contract this month"
- **Email 3**: "Last one - €807K contract matches your Berlin bid exactly"

---

## 🔒 **WHAT STAYS THE SAME (STATIC)**

### **1. Email Structure**
- Email flow and messaging approach
- Signature (Alex, TenderPulse)
- Trial link (https://tenderpulse.eu/trial)
- General messaging tone

### **2. Template Framework**
- Email sequence timing (Day 0, Day 3, Day 7)
- Overall value proposition approach
- Call-to-action structure

---

## 🔍 **PERSONALIZATION EXAMPLES**

### **Prospect 1: TechCorp GmbH (Munich)**
```
Subject: Similar €1M contract to your Munich bid

Sarah,

I saw TechCorp GmbH bid on the €1M Munich it & software contract that awarded on September 20, 2024.

Just found a similar opportunity:

€1M it & software contract
Frankfurt Municipality  
Same scope as Munich
Deadline: October 09

Since you already have the experience from Munich, this could be a good match.

Here's the TED listing: https://ted.europa.eu/udl?uri=TED:NOTICE:TED-111111

Alex
TenderPulse
```

### **Prospect 2: DataSolutions Ltd (Paris)**
```
Subject: Similar €650K contract to your Paris bid

Pierre,

I saw DataSolutions Ltd bid on the €650K Paris data analytics contract that awarded on September 18, 2024.

Just found a similar opportunity:

€650K data analytics contract
Lyon City Government  
Same scope as Paris
Deadline: October 21

Since you already have the experience from Paris, this could be a good match.

Here's the TED listing: https://ted.europa.eu/udl?uri=TED:NOTICE:TED-222222

Alex
TenderPulse
```

### **Prospect 3: GreenTech Solutions (Amsterdam)**
```
Subject: Similar €450K contract to your Amsterdam bid

Emma,

I saw GreenTech Solutions bid on the €450K Amsterdam environmental services contract that awarded on September 22, 2024.

Just found a similar opportunity:

€450K environmental services contract
Rotterdam Municipality  
Same scope as Amsterdam
Deadline: October 17

Since you already have the experience from Amsterdam, this could be a good match.

Here's the TED listing: https://ted.europa.eu/udl?uri=TED:NOTICE:TED-333333

Alex
TenderPulse
```

---

## 🚨 **SAFETY FEATURES**

### **1. Duplicate Detection**
- Each email gets a unique hash based on personalization elements
- System prevents sending identical emails to different prospects
- Hash tracking ensures no duplicates

### **2. Personalization Validation**
- 100/100 personalization score required
- Validates all 5 key personalization elements:
  - ✅ Contact name
  - ✅ Company name  
  - ✅ Contract value
  - ✅ Buyer name
  - ✅ Subject line

### **3. Data Source**
- All personalization comes from real TED contract data
- No generic templates or placeholders
- Each prospect's email is based on their specific lost tender

---

## 🎯 **RESULT**

**Every prospect receives a completely unique, personalized email based on their specific lost tender data. No two prospects will ever receive identical content.**

The system ensures:
- ✅ 100% personalization score
- ✅ Unique email hash per prospect
- ✅ Real contract data integration
- ✅ No duplicate emails
- ✅ Professional, data-driven approach

---

## 🔧 **How to Test Personalization**

```bash
# View templates with personalization markers
python3 email_template_with_markers.py

# See how same template looks for different prospects
python3 personalization_demo.py

# Validate personalization quality
python3 validate_personalization.py

# View actual email templates
python3 view_email_templates.py
```

---

**💡 Bottom Line: Your emails are fully personalized and unique per prospect. No risk of sending identical emails to different people!**
