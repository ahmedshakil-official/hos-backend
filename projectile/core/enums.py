from django.utils.translation import gettext as _

from enumerify.enum import Enum


class VatTaxStatus(Enum):
    DEFAULT = 1
    PRODUCT_WISE = 2

    i18n = (
        _('Default'),
        _('Product Wise'),
    )


class PaginationType(Enum):
    DEFAULT = 1
    SCROLL = 2

    i18n = (
        _('Default'),
        _('Scroll'),
    )


class ServiceConsumedPrintType(Enum):
    DEFAULT = 1
    SERVICE_CONSUMED_RECEIPT = 2

    i18n = (
        _('Default'),
        _('Service Consumed Receipt'),
    )


class ServiceConsumedReceiptType(Enum):
    WITH_QUANTITY = 1
    WITHOUT_QUANTITY = 2

    i18n = (
        _('With Quantity'),
        _('Without Quantity')
    )

class PersonDropoutStatus(Enum):
    DEFAULT = 1
    DEAD = 2
    MOVED_TO_ANOTHER_ORGANIZATION = 3

    i18n = (
        _('Default'),
        _('Dead'),
        _('Move to another organization')
    )


class PersonGender(Enum):
    MALE = 0
    FEMALE = 1
    TRANSSEXUAL = 2
    ANY = 3

    i18n = (
        _('Male'),
        _('Female'),
        _('Transsexual'),
        _('Any'),
    )


class EconomicGroup(Enum):
    EXTREME_POOR = 0
    POOR = 1
    LOWER_MIDDLE_CLASS = 4
    MIDDLE_CLASS = 2
    UPPER_MIDDLE_CLASS = 5
    RICH = 3
    EMERGENCY = 6

    i18n = (
        _('Extreme Poor'),
        _('Poor'),
        _('Middle Class'),
        _('Rich'),
        _('Lower Middle Class'),
        _('Upper Middle class'),
        _('Emergency')
    )


class PersonGroupType(Enum):
    PATIENT = 0
    EMPLOYEE = 1
    STACK_HOLDER = 2
    SUPPLIER = 3
    BOARD_OF_DIRECTOR = 4
    SYSTEM_ADMIN = 5
    REFERRER = 6
    SERVICE_PROVIDER = 7
    OTHER = 8
    PRESCRIBER = 9
    EXTRA = 10
    MONITOR = 11
    TRADER = 12
    CONTRACTOR = 13

    i18n = (
        _('Patient'),
        _('Employee'),
        _('Stack Holder'),
        _('Supplier'),
        _('Board of Director'),
        _('System Admin'),
        _('Referrer'),
        _('Service Provider'),
        _('Other'),
        _('Prescriber'),
        _('Extra'),
        _('Monitor'),
        _('Trader'),
        _('Contractor'),
    )


class PersonType(Enum):
    INTERNAL = 1
    EXTERNAL = 2

    i18n = (
        _('Internal'),
        _('External')
    )


class Relationship(Enum):
    FATHER = 0
    MOTHER = 1
    SPOUSE = 9
    BROTHER = 2
    SISTER = 3
    UNCLE = 10
    AUNT = 11
    BROTHER_IN_LAW = 4
    SISTER_IN_LAW = 5
    FATHER_IN_LAW = 6
    FRIENDS = 7
    HELPING_HAND = 8
    OTHER = 99

    i18n = (
        _('Father'),
        _('Mother'),
        _('Spouse'),
        _('Brother'),
        _('Sister'),
        _('Uncle'),
        _('Aunt'),
        _('Brother in Law'),
        _('Sister in Law'),
        _('Father in Law'),
        _('Friends'),
        _('Helping Hand'),
        _('Other'),
    )


class FamilyRelationship(Enum):
    SPOUSE = 1
    SON = 2
    DAUGHTER = 3
    SON_IN_LAW = 4
    DAUGHTER_IN_LAW = 5
    FATHER_IN_LAW = 6
    MOTHER_IN_LAW = 7
    NIECE = 8
    NEPHEW = 9
    UNCLE = 10
    AUNT = 11
    HEAD = 12
    OTHER = 13

    i18n = (
        _('Spouse'),
        _('Son'),
        _('Daughter'),
        _('Son in law'),
        _('Daughter in law'),
        _('Father in law'),
        _('Mother in law'),
        _('Niece'),
        _('Nephew'),
        _('Uncle'),
        _('Aunt'),
        _('Head'),
        _('Other'),
    )


class OrganizationType(Enum):
    MOTHER = 0
    BRANCH = 1
    UNITE = 2
    PRIVATE_PRACTITIONERS = 3
    PHARMACY = 4
    DIAGNOSTIC = 5
    DISTRIBUTOR = 6
    DISTRIBUTOR_BUYER = 7

    i18n = (
        _('Mother'),
        _('Branch'),
        _('Unite'),
        _('Private Practitioners'),
        _('Pharmacy'),
        _('Diagnostic'),
        _('Distributor'),
        _('Distributor Buyer'),
    )


class Themes(Enum):
    LIGHT = 0
    DARK = 1

    i18n = (
        _('Light'),
        _('Dark'),
    )


class TextSize(Enum):
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4

    i18n = (
        _('h1'),
        _('h2'),
        _('h3'),
        _('h4'),
    )


class JoiningInitiatorChoices(Enum):
    SALES = 1
    SERVICE = 2

    i18n = (
        _('Sales'),
        _('Service')
    )


class DatePickerType(Enum):
    DEFAULTDATEPICKER = 1
    GIVEINYEAR = 2

    i18n = (
        _('Default Date Picker'),
        _('Give In Year'),
    )


class SerialType(Enum):
    DEFAULT = 1     # Sytem  generated ID/Serial
    ORGANIZATION_WISE = 2    # Custome generated organization wise ID/Serial
    NO_SERIAL = 3    # NO ID/Serial

    i18n = (
        _('Default'),
        _('Organization Wise'),
        _('No Serial'),
    )


class DiscountType(Enum):
    FLAT = 1
    PERCENTAGE = 2

    i18n = (
        _('Flat'),
        _('Percentage')
    )


class PriceType(Enum):
    LATEST_PRICE = 1
    PRODUCT_PRICE = 2
    LATEST_PRICE_AND_PRODUCT_PRICE = 3
    PRODUCT_PRICE_AND_LATEST_PRICE = 4

    i18n = (
        _('Latest Price'),
        _('Product Price'),
        _('Latest Price and Product Price'),
        _('Product Price and Latest Price'),
    )


class SalaryType(Enum):
    BASIC_FROM_GROSS = 1
    GROSS_FROM_BASIC = 2

    i18n = (
        _('Basic From Gross'),
        _('Gross From Basic'),
    )


class PrintConfiguration(Enum):
    SWAL_OFF = 1
    SWAL_ON = 2

    i18n = (
        _('Sweet Alert Off'),
        _('Sweet Alert On'),
    )


class SalaryDisburseTypes(Enum):
    WEEKLY = 1
    MONTHLY = 2
    TRI_MONTHLY = 3
    YEARLY = 4

    i18n = (
        _('Weekly'),
        _('Monthly'),
        _('Tri Monthly'),
        _('Yearly'),
    )


class SalaryHeadType(Enum):
    ADDITION = 1
    DEDUCTION = 2

    i18n = (
        _('Addition'),
        _('Deduction'),
    )


class SalaryHeadDisburseType(Enum):
    SAVING = 1
    REGULAR_PAYMENT = 2
    REGULAR_EXPENSE = 3

    i18n = (
        _('Saving'),
        _('Regular Payment'),
        _('Regular Expense'),
    )


class Packages(Enum):
    PACKAGE_1 = 1
    PACKAGE_2 = 2
    PACKAGE_3 = 3

    i18n = (
        _('Package 1'),
        _('Package 2'),
        _('Package 3'),
    )


class EntryMode(Enum):
    ON = 1
    OFF = 2
    DONE = 3

    i18n = (
        _('ON'),
        _('OFF'),
        _('DONE'),
    )

class PatientInfoType(Enum):
    SHORT = 1
    DETAILS = 2

    i18n = (
        _('SHORT'),
        _('DETAILS'),
    )


class MaritalStatus(Enum):
    MARRIED = 1
    SINGLE = 2
    DIVORCED = 3
    WIDOWED = 4

    i18n = (
        _('Married'),
        _('Single'),
        _('Divorced'),
        _('Widowed'),
    )


class Religion(Enum):
    ISLAM = 1
    HINDU = 2
    CHRISTIAN = 3
    BUDDHIST = 4

    i18n = (
        _('Islam'),
        _('Hindu'),
        _('Christian'),
        _('Buddhist'),
    )


class EducationalQualification(Enum):
    ILLITERATE = 1
    BASIC = 2
    PRIMARY = 3
    UNDER_SSC = 4
    SSC_HSC = 5
    GRADUATE_MASTERS = 6
    POSTGRADUATE = 7

    i18n = (
        _('Illiterate'),
        _('Basic'),
        _('Primary'),
        _('Under SSC'),
        _('SSC / HSC'),
        _('Graduate / Masters'),
        _('PostGraduate'),
    )


class SmokingStatus(Enum):
    YES = 1
    NO = 2
    OTHER = 3

    i18n = (
        _('Yes'),
        _('No'),
        _('Other'),
    )

class BloodGroup(Enum):
    A_POSITIVE = 1
    A_NEGATIVE = 2
    B_POSITIVE = 3
    B_NEGATIVE = 4
    AB_POSITIVE = 5
    AB_NEGATIVE = 6
    O_POSITIVE = 7
    O_NEGATIVE = 8
    UNKNOWN = 9

    i18n = (
        _('A+'),
        _('A-'),
        _('B+'),
        _('B-'),
        _('AB+'),
        _('AB-'),
        _('O+'),
        _('O-'),
        _('Unknown'),
    )

class DhakaThana(Enum):
    ADABOR = 302602
    BADDA = 302604
    BANGSHAL = 302605
    BIMAN_BANDAR = 302606
    BANANI = 302607
    CANTONMENT = 302608
    CHAK_BAZAR = 302609
    DAKSHINKHAN = 302610
    DARUS_SALAM = 302611
    DEMRA = 302612
    DHAMRAI = 302614
    DHANMONDI = 302616
    DOHAR = 302618
    BHASAN_TEK = 302621
    BHATARA = 302622
    GENDARIA = 302624
    GULSHAN = 302626
    HAZARIBAGH = 302628
    JATRABARI = 302629
    KAFRUL = 302630
    KADAMTALI = 302632
    KALABAGAN = 302633
    KAMRANGIR_CHAR = 302634
    KHILGAON = 302636
    KHILKHET = 302637
    KERANIGANJ = 302638
    KOTWALI = 302640
    LALBAGH = 302642
    MIRPUR = 302648
    MOHAMMADPUR = 302650
    MOTIJHEEL = 302654
    MUGDA_PARA = 302657
    NAWABGANJ = 302662
    NEW_MARKET = 302663
    PALLABI = 302664
    PALTAN = 302665
    RAMNA = 302666
    RAMPURA = 302667
    SABUJBAGH = 302668
    RUPNAGAR = 302670
    SAVAR = 302672
    SHAHJAHANPUR = 302673
    SHAH_ALI = 302674
    SHAHBAGH = 302675
    SHYAMPUR = 302676
    SHER_E_BANGLA_NAGAR = 302680
    SUTRAPUR = 302688
    TEJGAON = 302690
    TEJGAON_IND_AREA = 302692
    TURAG = 302693
    UTTARA_PASCHIM = 302694
    UTTARA_PURBA = 302695
    UTTAR_KHAN = 302696
    WARI = 302698
    HATIRJHEEL = 888888
    OTHERS = 999999
    OUTSIDE_DHAKA = 777777
    i18n = (
        _('Adabor'),
        _('Badda'),
        _('Bangshal'),
        _('Biman Bandar'),
        _('Banani'),
        _('Cantonment'),
        _('Chak Bazar'),
        _('Dakshinkhan'),
        _('Darus Salam'),
        _('Demra'),
        _('Dhamrai'),
        _('Dhanmondi'),
        _('Dohar'),
        _('Bhasantek'),
        _('Bhatara'),
        _('Gendaria'),
        _('Gulshan'),
        _('Hazaribagh'),
        _('Jatrabari'),
        _('Kafrul'),
        _('Kadamtali'),
        _('Kalabagan'),
        _('Kamrangir Char'),
        _('Khilgaon'),
        _('Khilkhet'),
        _('Keraniganj'),
        _('Kotwali'),
        _('Lalbagh'),
        _('Mirpur'),
        _('Mohammadpur'),
        _('Motijheel'),
        _('Mugda Para'),
        _('Nawabganj'),
        _('Newmarket'),
        _('Pallabi'),
        _('Paltan'),
        _('Ramna'),
        _('Rampura'),
        _('Sabujbagh'),
        _('Rupnagar'),
        _('Savar'),
        _('Shahjahanpur'),
        _('Shah_ali'),
        _('Shahbagh'),
        _('Shyampur'),
        _('Sher-e-bangla Nagar'),
        _('Sutrapur'),
        _('Tejgaon'),
        _('Tejgaon Industrial Area'),
        _('Turag'),
        _('Uttara Paschim'),
        _('Uttara Purba'),
        _('Uttar Khan'),
        _('Wari'),
        _('Hatirjheel'),
        _('Others'),
        _('Outside Dhaka'),
    )


class IssueTrackingStatus(Enum):
    PENDING = 1
    ACCEPTED = 2
    PROCESSING = 3
    RESOLVED = 4
    REJECTED = 5

    i18n = (
        _('Pending'),
        _('Accepted'),
        _('Processing'),
        _('Resolved'),
        _('Rejected'),
    )


class IssueTypes(Enum):
    DELIVERY = 1
    RETURN = 2
    PRODUCT = 3
    PRICING = 4
    ORDER_CANCEL = 5
    OTHERS = 6

    i18n = (
        _('Delivery'),
        _('Return'),
        _('Product'),
        _('Pricing'),
        _('Order Cancel'),
        _('Others'),
    )


class FilePurposes(Enum):
    SCRIPT = 1
    DISTRIBUTOR_STOCK = 2
    PURCHASE_PREDICTION = 3
    OTHERS = 4

    i18n = (
        _('Script'),
        _('Distributor Stock'),
        _('Purchase Prediction'),
        _('Others'),
    )


class LoginFailureReason(Enum):
    WRONG_PASSWORD = 1
    INVALID_USER = 2
    OTHERS = 3

    i18n = (
        _('Wrong Password'),
        _('Invalid User'),
        _('Others'),
    )


class AllowOrderFrom(Enum):
    STOCK = 1
    STOCK_AND_NEXT_DAY = 2
    OPEN = 3
    STOCK_AND_OPEN = 4

    i18n = (
        _('Only Stock'),
        _('Stock and Next Day'),
        _('Open'),
        _("Stock and Open"),
    )