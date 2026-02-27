from datetime import datetime
import json
from statistics import mean

data = {
  "headerRecord": [
    {
      "reportDate": "062923",
      "reportTime": "143911",
      "preamble": "TCA7",
      "versionNo": "07",
      "mKeywordLength": "07",
      "mKeywordText": "SBMYSQL",
      "y2kReportedDate": "06292023"
    }
  ],
  "addressInformation": [
    {
      "city": "CALIFORNIA CITY",
      "dwellingType": "A",
      "firstReportedDate": "03172022",
      "lastReportingSubscriberCode": "1350240",
      "lastUpdatedDate": "05202022",
      "source": "2",
      "state": "CA",
      "streetName": "LOOP",
      "streetPrefix": "9817",
      "streetSuffix": "BLVD",
      "timesReported": "00",
      "unitId": "G",
      "unitType": "APT",
      "zipCode": "935051352"
    },
    {
      "city": "BURBANK",
      "dwellingType": "A",
      "firstReportedDate": "12182020",
      "lastUpdatedDate": "03192021",
      "source": "1",
      "state": "CA",
      "streetName": "OLIVE",
      "streetPrefix": "450 E",
      "streetSuffix": "AVE",
      "timesReported": "00",
      "unitId": "339",
      "unitType": "APT",
      "zipCode": "915013320"
    },
    {
      "city": "LOS ANGELES",
      "dwellingType": "S",
      "firstReportedDate": "03012006",
      "lastUpdatedDate": "11122020",
      "source": "1",
      "state": "CA",
      "streetName": "CIMARRON",
      "streetPrefix": "4427",
      "streetSuffix": "ST",
      "timesReported": "17",
      "zipCode": "900621916"
    }
  ],
  "consumerIdentity": {
    "name": [
      {
        "firstName": "LAURIE",
        "surname": "ANDERSON",
        "type": "N"
      },
      {
        "firstName": "LAURIE",
        "surname": "ANDERSON",
        "type": "S"
      },
      {
        "firstName": "LAURIE",
        "middleName": "ANNE",
        "surname": "BERTHA",
        "type": "A"
      },
      {
        "firstName": "LAURIE",
        "surname": "FULLER",
        "type": "A"
      }
    ]
  },
  "employmentInformation": [
    {
      "firstReportedDate": "05282020",
      "lastUpdatedDate": "05282020",
      "name": "PANARAM INTERNATIONAL",
      "source": "2"
    },
    {
      "firstReportedDate": "07052015",
      "lastUpdatedDate": "07052015",
      "name": "RETIRED",
      "source": "2"
    }
  ],
  "informationalMessage": [
    {
      "messageNumber": "84",
      "messageNumberDetailed": "0084",
      "messageText": "SSN MATCHES"
    },
    {
      "messageNumber": "57",
      "messageNumberDetailed": "0335",
      "messageText": "F908TOO MANY INQUIRIES LAST 12 MONTHS"
    }
  ],
  "inquiry": [
    {
      "amount": "UNKNOWN",
      "date": "01282023",
      "subscriberCode": "3970658",
      "subscriberName": "SERVICE & PROF",
      "terms": "UNK",
      "type": "08"
    },
    {
      "amount": "UNKNOWN",
      "date": "05132021",
      "kob": "YC",
      "subscriberCode": "1984208",
      "subscriberName": "OTHER COLLECTION AGENC",
      "terms": "UNK",
      "type": "48"
    },
    {
      "amount": "UNKNOWN",
      "date": "05132021",
      "kob": "YC",
      "subscriberCode": "1984518",
      "subscriberName": "OTHER COLLECTION AGENC",
      "terms": "UNK",
      "type": "48"
    }
  ],
  "ofac": {
    "messageNumber": "1199",
    "messageText": "OFAC SEARCH NOT PERFORMED DUE TO MISMATCHED YOB/DOB"
  },
  "publicRecord": [
    {
      "courtCode": "2001065",
      "courtName": "US BKPT CT MS GULFPORT",
      "ecoa": "1",
      "evaluation": "N",
      "filingDate": "09022020",
      "referenceNumber": "0352321ERG",
      "status": "15",
      "statusDate": "12272020"
    }
  ],
  "riskModel": [
    {
      "evaluation": "P",
      "modelIndicator": "F9",
      "score": "0650",
      "scoreFactors": [
        {
          "importance": "1",
          "code": "40"
        },
        {
          "importance": "2",
          "code": "33"
        },
        {
          "importance": "3",
          "code": "24"
        },
        {
          "importance": "4",
          "code": "15"
        },
        {
          "importance": "5",
          "code": "08"
        }
      ]
    }
  ],
  "tradeline": [
    {
      "accountNumber": "46725120705550",
      "accountType": "12",
      "amount1": "00003244",
      "amount1Qualifier": "O",
      "balanceDate": "12132021",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "enhancedAccountCondition": "05",
        "enhancedAccountType": "12",
        "enhancedPaymentHistory84": "BCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedSpecialComment": "51",
        "enhancedTerms": "117",
        "enhancedTermsFrequency": "M",
        "originalLoanAmount": "0000003244",
        "paymentLevelDate": "12012021"
      },
      "evaluation": "N",
      "kob": "EL",
      "monthsHistory": "09",
      "openDate": "12132020",
      "openOrClosed": "C",
      "paymentHistory": "BCCCCCCCC",
      "revolvingOrInstallment": "I",
      "specialComment": "28",
      "status": "05",
      "statusDate": "12012021",
      "subscriberCode": "6908265",
      "subscriberName": "MOHELA",
      "terms": "117"
    },
    {
      "accountNumber": "46725120705556",
      "accountType": "12",
      "amount1": "00005304",
      "amount1Qualifier": "O",
      "balanceDate": "12132021",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "enhancedAccountCondition": "05",
        "enhancedAccountType": "12",
        "enhancedPaymentHistory84": "BCCCCCCCCCCCCCCCCCCCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedSpecialComment": "51",
        "enhancedTerms": "117",
        "enhancedTermsFrequency": "M",
        "originalLoanAmount": "0000005304",
        "paymentLevelDate": "12012021"
      },
      "evaluation": "N",
      "kob": "EL",
      "monthsHistory": "27",
      "openDate": "01112019",
      "openOrClosed": "C",
      "paymentHistory": "BCCCCCCCCCCCCCCCCCCCCCCCC",
      "revolvingOrInstallment": "I",
      "specialComment": "28",
      "status": "05",
      "statusDate": "12012021",
      "subscriberCode": "6908265",
      "subscriberName": "MOHELA",
      "terms": "117"
    },
    {
      "accountNumber": "46725120705557",
      "accountType": "12",
      "amount1": "00002369",
      "amount1Qualifier": "O",
      "balanceDate": "12132021",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "enhancedAccountCondition": "05",
        "enhancedAccountType": "12",
        "enhancedPaymentHistory84": "BCCCCCCCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedSpecialComment": "51",
        "enhancedTerms": "117",
        "enhancedTermsFrequency": "M",
        "originalLoanAmount": "0000002369",
        "paymentLevelDate": "12012021"
      },
      "evaluation": "N",
      "kob": "EL",
      "monthsHistory": "15",
      "openDate": "12142019",
      "openOrClosed": "C",
      "paymentHistory": "BCCCCCCCCCCCCCC",
      "revolvingOrInstallment": "I",
      "specialComment": "28",
      "status": "05",
      "statusDate": "12012021",
      "subscriberCode": "6908265",
      "subscriberName": "MOHELA",
      "terms": "117"
    },
    {
      "accountNumber": "46725120705558",
      "accountType": "12",
      "amount1": "00006323",
      "amount1Qualifier": "O",
      "balanceDate": "12132021",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "enhancedAccountCondition": "05",
        "enhancedAccountType": "12",
        "enhancedPaymentHistory84": "BCCCCCCCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedSpecialComment": "51",
        "enhancedTerms": "117",
        "enhancedTermsFrequency": "M",
        "originalLoanAmount": "0000006323",
        "paymentLevelDate": "12012021"
      },
      "evaluation": "N",
      "kob": "EL",
      "monthsHistory": "15",
      "openDate": "12142019",
      "openOrClosed": "C",
      "paymentHistory": "BCCCCCCCCCCCCCC",
      "revolvingOrInstallment": "I",
      "specialComment": "28",
      "status": "05",
      "statusDate": "12012021",
      "subscriberCode": "6908265",
      "subscriberName": "MOHELA",
      "terms": "117"
    },
    {
      "accountNumber": "46725120705559",
      "accountType": "12",
      "amount1": "00001506",
      "amount1Qualifier": "O",
      "balanceDate": "12132021",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "enhancedAccountCondition": "05",
        "enhancedAccountType": "12",
        "enhancedPaymentHistory84": "BCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedSpecialComment": "51",
        "enhancedTerms": "117",
        "enhancedTermsFrequency": "M",
        "originalLoanAmount": "0000001506",
        "paymentLevelDate": "12012021"
      },
      "evaluation": "N",
      "kob": "EL",
      "monthsHistory": "09",
      "openDate": "12132020",
      "openOrClosed": "C",
      "paymentHistory": "BCCCCCCCC",
      "revolvingOrInstallment": "I",
      "specialComment": "28",
      "status": "05",
      "statusDate": "12012021",
      "subscriberCode": "6908265",
      "subscriberName": "MOHELA",
      "terms": "117"
    },
    {
      "accountNumber": "4760947509985",
      "accountType": "07",
      "amount1": "00001000",
      "amount1Qualifier": "L",
      "balanceDate": "01192015",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "creditLimitAmount": "0000001000",
        "enhancedAccountCondition": "A3",
        "enhancedAccountType": "07",
        "enhancedPaymentHistory84": "B0-000000000000000000000000000000000000000",
        "enhancedPaymentStatus": "11",
        "enhancedTerms": "REV",
        "highBalanceAmount": "0000000000",
        "paymentLevelDate": "01012015"
      },
      "evaluation": "P",
      "kob": "ZR",
      "monthsHistory": "81",
      "openDate": "05112008",
      "openOrClosed": "C",
      "paymentHistory": "B0-0000000000000000000000",
      "revolvingOrInstallment": "R",
      "status": "11",
      "statusDate": "01012015",
      "subscriberCode": "1392176",
      "subscriberName": "MACYS/FDSB",
      "terms": "REV"
    },
    {
      "accountNumber": "0018610978",
      "accountType": "18",
      "amount1": "00000500",
      "amount1Qualifier": "L",
      "amount2": "00000578",
      "amount2Qualifier": "H",
      "balanceDate": "02222023",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "3",
      "enhancedPaymentData": {
        "complianceCondition": "XA",
        "creditLimitAmount": "0000000500",
        "enhancedAccountCondition": "A2",
        "enhancedAccountType": "18",
        "enhancedPaymentHistory84": "B0CCCCCCCCCCCCCCCCCCCCCCCC0",
        "enhancedPaymentStatus": "11",
        "enhancedSpecialComment": "19",
        "enhancedTerms": "REV",
        "enhancedTermsFrequency": "M",
        "highBalanceAmount": "0000000578",
        "paymentLevelDate": "02012023"
      },
      "evaluation": "N",
      "kob": "BC",
      "lastPaymentDate": "01202023",
      "monthsHistory": "27",
      "openDate": "12282020",
      "openOrClosed": "C",
      "paymentHistory": "B0CCCCCCCCCCCCCCCCCCCCCCC",
      "revolvingOrInstallment": "R",
      "specialComment": "19",
      "status": "12",
      "statusDate": "02012023",
      "subscriberCode": "3200714",
      "subscriberName": "CAPITAL ONE",
      "terms": "REV"
    },
    {
      "accountNumber": "302490966",
      "accountType": "18",
      "amount1": "00000850",
      "amount1Qualifier": "L",
      "amount2": "00000845",
      "amount2Qualifier": "H",
      "balanceDate": "01122023",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "3",
      "enhancedPaymentData": {
        "complianceCondition": "XA",
        "creditLimitAmount": "0000000850",
        "enhancedAccountCondition": "A2",
        "enhancedAccountType": "18",
        "enhancedPaymentHistory84": "B0CCCCCCCCCCCCCCCCCCCCCCCC00CC00CCCCCCCC0C0CCC000",
        "enhancedPaymentStatus": "11",
        "enhancedSpecialComment": "19",
        "enhancedTerms": "REV",
        "enhancedTermsFrequency": "M",
        "highBalanceAmount": "0000000845",
        "paymentLevelDate": "01012023"
      },
      "evaluation": "N",
      "kob": "BC",
      "lastPaymentDate": "11262022",
      "monthsHistory": "49",
      "openDate": "01012019",
      "openOrClosed": "C",
      "paymentHistory": "B0CCCCCCCCCCCCCCCCCCCCCCC",
      "revolvingOrInstallment": "R",
      "specialComment": "19",
      "status": "12",
      "statusDate": "01012023",
      "subscriberCode": "1232900",
      "subscriberName": "CITI/CBNA",
      "terms": "REV"
    },
    {
      "accountNumber": "529115167349",
      "accountType": "18",
      "amount1": "00001224",
      "amount1Qualifier": "H",
      "balanceDate": "06162020",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "3",
      "enhancedPaymentData": {
        "complianceCondition": "XA",
        "creditLimitAmount": "UNKNOWN",
        "enhancedAccountCondition": "A2",
        "enhancedAccountType": "18",
        "enhancedPaymentHistory84": "BCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedSpecialComment": "19",
        "enhancedTerms": "REV",
        "enhancedTermsFrequency": "M",
        "highBalanceAmount": "0000001224",
        "paymentLevelDate": "06012020"
      },
      "evaluation": "N",
      "kob": "BC",
      "monthsHistory": "36",
      "openDate": "07252017",
      "openOrClosed": "C",
      "paymentHistory": "BCCCCCCCCCCCCCCCCCCCCCCCC",
      "revolvingOrInstallment": "R",
      "specialComment": "19",
      "status": "12",
      "statusDate": "06012020",
      "subscriberCode": "1270246",
      "subscriberName": "CAPITAL ONE",
      "terms": "REV"
    },
    {
      "accountNumber": "4417122374688936",
      "accountType": "18",
      "amount1": "00010000",
      "amount1Qualifier": "L",
      "amount2": "00010000",
      "amount2Qualifier": "H",
      "balanceDate": "05172019",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "3",
      "enhancedPaymentData": {
        "creditLimitAmount": "0000010000",
        "enhancedAccountCondition": "A2",
        "enhancedAccountType": "18",
        "enhancedPaymentHistory84": "BB0B---------------B-00000000000000000000000000000-0---------------000",
        "enhancedPaymentStatus": "11",
        "enhancedSpecialComment": "18",
        "enhancedTerms": "REV",
        "enhancedTermsFrequency": "M",
        "highBalanceAmount": "0000010000",
        "paymentLevelDate": "04012019"
      },
      "evaluation": "N",
      "kob": "BC",
      "monthsHistory": "70",
      "openDate": "10052012",
      "openOrClosed": "C",
      "paymentHistory": "BB0B---------------B-0000",
      "revolvingOrInstallment": "R",
      "specialComment": "18",
      "status": "12",
      "statusDate": "04012019",
      "subscriberCode": "1310331",
      "subscriberName": "JPMCB CARD",
      "terms": "REV"
    },
    {
      "accountNumber": "4111427308",
      "accountType": "13",
      "amount1": "00070807",
      "amount1Qualifier": "O",
      "balanceDate": "12282013",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "enhancedAccountCondition": "A2",
        "enhancedAccountType": "13",
        "enhancedPaymentHistory84": "BCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedTerms": "048",
        "originalLoanAmount": "0000070807",
        "paymentLevelDate": "12012013"
      },
      "evaluation": "P",
      "kob": "BB",
      "monthsHistory": "06",
      "openDate": "07012013",
      "openOrClosed": "C",
      "paymentHistory": "BCCCCC",
      "revolvingOrInstallment": "I",
      "status": "12",
      "statusDate": "12012013",
      "subscriberCode": "1102013",
      "subscriberName": "JPMCB AUTO",
      "terms": "048"
    },
    {
      "accountNumber": "4266841056723057",
      "accountType": "18",
      "amount1": "00006500",
      "amount1Qualifier": "L",
      "amount2": "00006512",
      "amount2Qualifier": "H",
      "balanceAmount": "00004066",
      "balanceDate": "04242023",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "3",
      "enhancedPaymentData": {
        "actualPaymentAmount": "00002300",
        "creditLimitAmount": "0000006500",
        "enhancedAccountCondition": "A1",
        "enhancedAccountType": "18",
        "enhancedPaymentHistory84": "CCCC",
        "enhancedPaymentStatus": "11",
        "enhancedTerms": "REV",
        "enhancedTermsFrequency": "M",
        "highBalanceAmount": "0000006512",
        "paymentLevelDate": "04012023"
      },
      "evaluation": "P",
      "kob": "BC",
      "lastPaymentDate": "04092023",
      "monthlyPaymentAmount": "00000081",
      "monthlyPaymentType": "S",
      "monthsHistory": "04",
      "openDate": "12252022",
      "openOrClosed": "O",
      "paymentHistory": "CCCC",
      "revolvingOrInstallment": "R",
      "status": "11",
      "statusDate": "04012023",
      "subscriberCode": "3182310",
      "subscriberName": "JPMCB CARD",
      "terms": "REV"
    },
    {
      "accountNumber": "7088777827",
      "accountType": "18",
      "amount1": "00002000",
      "amount1Qualifier": "L",
      "amount2": "00001661",
      "amount2Qualifier": "H",
      "balanceAmount": "00001602",
      "balanceDate": "04232023",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "3",
      "enhancedPaymentData": {
        "creditLimitAmount": "0000002000",
        "enhancedAccountCondition": "A1",
        "enhancedAccountType": "18",
        "enhancedPaymentHistory84": "CCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedTerms": "REV",
        "highBalanceAmount": "0000001661",
        "paymentLevelDate": "04012023"
      },
      "evaluation": "P",
      "kob": "BC",
      "lastPaymentDate": "04072023",
      "monthlyPaymentAmount": "00000049",
      "monthlyPaymentType": "S",
      "monthsHistory": "05",
      "openDate": "11222022",
      "openOrClosed": "O",
      "paymentHistory": "CCCCC",
      "revolvingOrInstallment": "R",
      "status": "11",
      "statusDate": "04012023",
      "subscriberCode": "3208430",
      "subscriberName": "BANK CREDIT CARD",
      "terms": "REV"
    },
    {
      "accountNumber": "6035320150871529",
      "accountType": "07",
      "amount1": "00000500",
      "amount1Qualifier": "L",
      "amount2": "00000511",
      "amount2Qualifier": "H",
      "balanceAmount": "00000000",
      "balanceDate": "04052023",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "0",
      "enhancedPaymentData": {
        "creditLimitAmount": "0000000500",
        "enhancedAccountCondition": "A1",
        "enhancedAccountType": "07",
        "enhancedPaymentHistory84": "00CCCCCCCCCCCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedTerms": "REV",
        "enhancedTermsFrequency": "M",
        "highBalanceAmount": "0000000511",
        "paymentLevelDate": "04012023"
      },
      "evaluation": "P",
      "kob": "ZR",
      "lastPaymentDate": "01252023",
      "monthsHistory": "20",
      "openDate": "08272021",
      "openOrClosed": "O",
      "paymentHistory": "00CCCCCCCCCCCCCCCCCC",
      "revolvingOrInstallment": "R",
      "status": "11",
      "statusDate": "04012023",
      "subscriberCode": "3178962",
      "subscriberName": "THD/CBNA",
      "terms": "REV"
    },
    {
      "accountNumber": "46725120705556",
      "accountType": "12",
      "amount1": "00009666",
      "amount1Qualifier": "O",
      "balanceAmount": "00009566",
      "balanceDate": "11032022",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "enhancedAccountCondition": "A1",
        "enhancedAccountType": "12",
        "enhancedPaymentHistory84": "CCCCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedTerms": "179",
        "enhancedTermsFrequency": "M",
        "originalLoanAmount": "0000009666",
        "paymentLevelDate": "11012022"
      },
      "evaluation": "P",
      "kob": "EL",
      "lastPaymentDate": "10282022",
      "monthlyPaymentAmount": "00000027",
      "monthlyPaymentType": "S",
      "monthsHistory": "11",
      "openDate": "12042021",
      "openOrClosed": "O",
      "paymentHistory": "CCCCCCCCCCC",
      "revolvingOrInstallment": "I",
      "status": "11",
      "statusDate": "11012022",
      "subscriberCode": "8997779",
      "subscriberName": "MOHELA",
      "terms": "179"
    },
    {
      "accountNumber": "46725120705557",
      "accountType": "12",
      "amount1": "00009042",
      "amount1Qualifier": "O",
      "balanceAmount": "00008948",
      "balanceDate": "11032022",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "enhancedAccountCondition": "A1",
        "enhancedAccountType": "12",
        "enhancedPaymentHistory84": "CCCCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedTerms": "179",
        "enhancedTermsFrequency": "M",
        "originalLoanAmount": "0000009042",
        "paymentLevelDate": "11012022"
      },
      "evaluation": "P",
      "kob": "EL",
      "lastPaymentDate": "10282022",
      "monthlyPaymentAmount": "00000025",
      "monthlyPaymentType": "S",
      "monthsHistory": "11",
      "openDate": "12042021",
      "openOrClosed": "O",
      "paymentHistory": "CCCCCCCCCCC",
      "revolvingOrInstallment": "I",
      "status": "11",
      "statusDate": "11012022",
      "subscriberCode": "8997779",
      "subscriberName": "MOHELA",
      "terms": "179"
    },
    {
      "accountNumber": "5411853424",
      "accountType": "07",
      "amount1": "00001219",
      "amount1Qualifier": "L",
      "amount2": "00000618",
      "amount2Qualifier": "C",
      "balanceAmount": "00000000",
      "balanceDate": "03282015",
      "delinquencies30Days": "00",
      "delinquencies60Days": "00",
      "delinquencies90to180Days": "00",
      "derogCounter": "00",
      "ecoa": "1",
      "enhancedPaymentData": {
        "chargeoffAmount": "0000000618",
        "creditLimitAmount": "0000001219",
        "enhancedAccountCondition": "A4",
        "enhancedAccountType": "07",
        "enhancedPaymentHistory84": "0-------CCCCCCCCCCCCCCCCCC",
        "enhancedPaymentStatus": "11",
        "enhancedTerms": "REV",
        "highBalanceAmount": "0000001199",
        "paymentLevelDate": "03012015"
      },
      "evaluation": "P",
      "kob": "BC",
      "lastPaymentDate": "02192014",
      "monthsHistory": "26",
      "openDate": "03072013",
      "openOrClosed": "O",
      "paymentHistory": "0-------CCCCCCCCCCCCCCCCC",
      "revolvingOrInstallment": "R",
      "status": "11",
      "statusDate": "03012015",
      "subscriberCode": "2225419",
      "subscriberName": "BANK CREDIT CARD",
      "terms": "REV"
    }
  ],
  "endTotals": [
    {
      "totalSegments": "036",
      "totalLength": "07160"
    }
  ]
}

class CreditSummaryGenerator:

    def __init__(self, data: dict):
        self.data = data
        self.tradelines = data.get("tradeline", [])
        self.risk_models = data.get("riskModel", [])

    @staticmethod
    def parse_int(v):
        if v is None:
            return 0
        if isinstance(v, str):
            v = v.replace("UNKNOWN", "0")
            return int(v) if v.isdigit() else 0
        return int(v)

    @staticmethod
    def parse_date(d):
        if not d:
            return None
        return datetime.strptime(d, "%m%d%Y")

    def generate_credit_report(self):

        total_accounts = len(self.tradelines)
        active_accounts = 0
        closed_accounts = 0

        revolving = 0
        installment = 0

        total_balance = 0
        total_limit = 0
        total_monthly_payment = 0

        d30 = d60 = d90 = 0
        accounts_with_late = 0
        severe_accounts = 0

        open_dates = []

        for t in self.tradelines:

            # lifecycle
            if t.get("openOrClosed") == "O":
                active_accounts += 1
            else:
                closed_accounts += 1

            # mix
            if t.get("revolvingOrInstallment") == "R":
                revolving += 1
            elif t.get("revolvingOrInstallment") == "I":
                installment += 1

            # balances
            bal = self.parse_int(t.get("balanceAmount"))
            total_balance += bal

            monthly = self.parse_int(t.get("monthlyPaymentAmount"))
            total_monthly_payment += monthly

            # limit
            limit = self.parse_int(
                t.get("enhancedPaymentData", {}).get("creditLimitAmount")
            )
            total_limit += limit

            # delinquency
            d30 += self.parse_int(t.get("delinquencies30Days"))
            d60 += self.parse_int(t.get("delinquencies60Days"))
            d90 += self.parse_int(t.get("delinquencies90to180Days"))

            if (
                self.parse_int(t.get("delinquencies30Days")) > 0
                or self.parse_int(t.get("delinquencies60Days")) > 0
                or self.parse_int(t.get("delinquencies90to180Days")) > 0
            ):
                accounts_with_late += 1

            if self.parse_int(t.get("delinquencies90to180Days")) > 0:
                severe_accounts += 1

            # dates
            od = self.parse_date(t.get("openDate"))
            if od:
                open_dates.append(od)

        utilization = total_balance / total_limit if total_limit else 0

        oldest = min(open_dates) if open_dates else None
        newest = max(open_dates) if open_dates else None

        avg_age = None
        if open_dates:
            today = datetime.today()
            ages = [(today - d).days / 30 for d in open_dates]
            avg_age = mean(ages)

        # score
        score = None
        model = None
        factors = []

        if self.risk_models:
            rm = self.risk_models[0]
            score = rm.get("score")
            model = rm.get("modelIndicator")
            factors = rm.get("scoreFactors", [])

        return {
            "consumer_summary": {
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "closed_accounts": closed_accounts,
                "total_revolving": revolving,
                "total_installment": installment,
            },
            "debt_summary": {
                "total_balance": total_balance,
                "total_credit_limit": total_limit,
                "utilization_ratio": round(utilization, 3),
                "total_monthly_payment": total_monthly_payment,
            },
            "delinquency_summary": {
                "accounts_with_late": accounts_with_late,
                "total_30": d30,
                "total_60": d60,
                "total_90_plus": d90,
                "severe_accounts": severe_accounts,
            },
            "account_age": {
                "oldest_account": oldest.isoformat() if oldest else None,
                "newest_account": newest.isoformat() if newest else None,
                "avg_age_months": round(avg_age, 3) if avg_age else None,
            },
            "score": {
                "model": model,
                "value": score,
                "factors": factors,
            },
            "terms":{
                "revolving": "Credit that you can use again after paying.",
                "installment": "Credit that you must pay back over time.",
                "total_monthly_payment": "The amount of money you must pay back each month.",
                "closed_accounts": "Accounts that have been closed and can't be used.",
                "model": "Model used to calculate your credit score.",
                "value": "Your credit score."
            }
        }
        
# obj = CreditSummaryGenerator(data)
# print(obj.generate_credit_report())

obj = CreditSummaryGenerator(data)
response = obj.generate_credit_report()
with open("credit_summary.json", "w") as f:
    json.dump(response, f, indent=2)