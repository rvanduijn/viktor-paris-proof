from viktor import ViktorController
from viktor.parametrization import ViktorParametrization, TextField, Section, SetParamsButton, LineBreak, Text, \
    OptionField, OptionListElement, Image, Step
from viktor.geometry import SquareBeam, Material
from viktor.views import GeometryView, GeometryResult, Color, DataGroup, DataItem, DataResult, DataView, \
    GeometryAndDataView, GeometryAndDataResult, WebView, WebResult
from viktor.parametrization import NumberField
import math
from pathlib import Path

from viktor.external.word import render_word_file, WordFileTag
from viktor.utils import convert_word_to_pdf
from viktor.views import PDFResult, PDFView
from viktor.parametrization import TextField, DateField, Text
# viktor-cli publish --registered-name paris-proof-app  --tag v0.2.3



class ParisProofApp(object):
    def __init__(self, BVO_office, BVO_warehouse, office_perc, solar_panels_percentage, solar_split):
        self.BVO_office = BVO_office
        self.BVO_warehouse = BVO_warehouse
        self.sqm_total = BVO_office + BVO_warehouse
        self.GO_office = BVO_office * 0.95
        self.GO_warehouse = BVO_warehouse * 0.97
        self.perc_office = office_perc
        self.perc_warehouse = 1 - office_perc

        # ventilation_factor parameters:
        self.sqm_pp = 22
        self.vent_requirements_pp = 40
        self.vent_fact_m2 = 0.25
        self.vent_operating_hours = 2000

        # cooling_factor parameters
        self.cf_watt_p_m2_office = 60
        self.cf_operating_hours_office = 800
        self.cf_COP = 1  # 3

        # heat_loss_factor
        self.hl_watt_p_m2_office = 40
        self.hl_operating_hours_office = 1100
        self.hl_watt_p_m2_warehouse = 10
        self.hl_operating_hours_warehouse = 500
        self.hl_COP = 4

        # lighting_usage
        self.lighting_operating_hours = 2000
        self.lighting_watt_p_m2_office = 4
        self.lighting_watt_p_m2_warehouse = 2.5

        # own_usage
        self.ou_kWh_p_m2_office = 10
        self.ou_kWh_p_m2_warehouse = 5

        # solar_panels_yield
        self.fill_percentage_warehouse = solar_panels_percentage  # 0.115
        self.panel_size = 2
        self.panel_watt_peak = 420
        self.watt_to_kWh = self.panel_watt_peak * 0.8
        self.solar_split = solar_split

        # paris_proof
        self.pp_labels = ['Paris Proof', 'Zeer Zuinig', 'Zuinig', 'Gemiddeld', 'Onzuinig', 'Zeer onzuinig']
        self.pp_office_ranges = [70, 100, 150, 230, 330]
        self.pp_warehouse_ranges = [-25, -10, 20, 70, 115]
        self.data = {
            'BVO_office': self.BVO_office,
            'BVO_warehouse': self.BVO_warehouse,
        }

    def ventilation_factor(self):
        nro_people = math.ceil(self.BVO_office / self.sqm_pp)
        total_vent = nro_people * self.vent_requirements_pp
        total_Ewatt = total_vent * self.vent_fact_m2 * self.vent_operating_hours
        total_EkWh = total_Ewatt / 1000

        return total_EkWh

    def cooling_factor(self, watt_p_m2, operating_hours, COP):
        total_watt = watt_p_m2 * self.BVO_office * operating_hours
        total_kWh = total_watt / 1000

        total_Ekwh = total_kWh / COP

        return total_Ekwh

    def heat_loss_factor(self, watt_p_m2, operating_hours, COP):
        total_watt = watt_p_m2 * self.BVO_office * operating_hours
        total_kWh = total_watt / 1000

        total_Ekwh = total_kWh / COP

        return total_Ekwh

    def lighting_usage(self, watt_p_m2, operating_hours, GO):
        total_ewatt = watt_p_m2 * GO * operating_hours
        total_EkWh = total_ewatt / 1000

        return total_EkWh

    def own_usage(self, watt_p_m2, GO):
        total_EkWh = watt_p_m2 * GO

        return total_EkWh

    def solar_panels_yield(self):
        nro_panels = math.ceil((self.BVO_warehouse * self.fill_percentage_warehouse) / self.panel_size)
        total_EkWh = nro_panels * self.watt_to_kWh

        return total_EkWh

    def find_index(self, lst, value):
        index = 0
        while index < len(lst) and lst[index] < value:
            index += 1
        paris_proof = self.pp_labels[index]
        return paris_proof
    
    def calc_office(self):
        total_vent_office = self.ventilation_factor() * self.perc_warehouse
        total_cf_office = (self.cooling_factor(self.cf_watt_p_m2_office, self.cf_operating_hours_office,
                                                  self.cf_COP)) * self.perc_office
        total_hl_office = self.heat_loss_factor(self.hl_watt_p_m2_office, self.hl_operating_hours_office,
                                                   self.hl_COP)
        total_lighting_office = self.lighting_usage(self.lighting_watt_p_m2_office, self.lighting_operating_hours,
                                                       self.GO_office)
        total_own_usage_office = self.own_usage(self.ou_kWh_p_m2_office, self.GO_office)

        office_total_kWh = total_vent_office + total_cf_office + total_hl_office + total_lighting_office + total_own_usage_office
        office_yield_kWh = self.solar_panels_yield() * self.solar_split
        office_difference_kWh = office_total_kWh - office_yield_kWh
        office_difference_kWh_m2 = round(office_difference_kWh / self.BVO_office, 2)
        office_co2 = office_total_kWh * 0.37
        office_cost = office_total_kWh * 0.25
        paris_proof = self.find_index(self.pp_office_ranges, office_difference_kWh_m2)

        dict_results = {
            'office_ventilation': round(total_vent_office, 2),
            'office_cooling_factor': round(total_cf_office, 2),
            'office_heat_loss': round(total_hl_office, 2),
            'office_lighting': round(total_lighting_office, 2),
            'office_own_usage': round(total_own_usage_office, 2),
            'office_total_kWh': round(office_total_kWh, 2),
            'office_yield_kWh': round(office_yield_kWh, 2),
            'office_difference_kWh': round(office_difference_kWh, 2),
            'office_difference_kWh_m2': round(office_difference_kWh_m2, 2),
            'office_co2': round(office_co2, 2),
            'office_cost': round(office_cost, 2),
            'office_paris-proof': paris_proof,
        }

        self.data.update(dict_results)

    def calc_warehouse(self):
        total_vent_warehouse = self.ventilation_factor() * self.perc_warehouse
        total_cf_warehouse = (self.cooling_factor(self.cf_watt_p_m2_office, self.cf_operating_hours_office, self.cf_COP)) * self.perc_warehouse
        total_hl_warehouse = self.heat_loss_factor(self.hl_watt_p_m2_warehouse, self.hl_operating_hours_warehouse, self.hl_COP)
        total_lighting_warehouse = self.lighting_usage(self.lighting_watt_p_m2_warehouse, self.lighting_operating_hours, self.GO_warehouse)
        total_own_usage_warehouse = self.own_usage(self.ou_kWh_p_m2_warehouse, self.GO_warehouse)
        
        warehouse_total_kWh = total_vent_warehouse + total_cf_warehouse + total_hl_warehouse + total_lighting_warehouse + total_own_usage_warehouse
        warehouse_yield_kWh = self.solar_panels_yield() * (1 - self.solar_split)
        warehouse_difference_kWh = warehouse_total_kWh - warehouse_yield_kWh
        warehouse_difference_kWh_m2 = round(warehouse_difference_kWh / self.BVO_warehouse, 2)
        warehouse_co2 = warehouse_total_kWh * 0.37
        warehouse_cost = warehouse_total_kWh * 0.25

        paris_proof = self.find_index(self.pp_warehouse_ranges, warehouse_difference_kWh_m2)

        dict_results = {
            'warehouse_ventilation': round(total_vent_warehouse, 2),
            'warehouse_cooling_factor': round(total_cf_warehouse, 2),
            'warehouse_heat_loss': round(total_hl_warehouse, 2),
            'warehouse_lighting': round(total_lighting_warehouse, 2),
            'warehouse_own_usage': round(total_own_usage_warehouse, 2),
            'warehouse_total_kWh': round(warehouse_total_kWh, 2),
            'warehouse_yield_kWh': round(warehouse_yield_kWh, 2),
            'warehouse_difference_kWh': round(warehouse_difference_kWh, 2),
            'warehouse_difference_kWh_m2': round(warehouse_difference_kWh_m2, 2),
            'warehouse_co2': round(warehouse_co2, 2),
            'warehouse_cost': round(warehouse_cost, 2),
            'warehouse_paris-proof': paris_proof,
        }
        self.data.update(dict_results)

    def app_run(self):

        self.calc_office()
        self.calc_warehouse()

        return self.data


class Parametrization(ViktorParametrization):
    tab_1 = Step('Klik op "Volgende stap" om naar de Paris Proof app te gaan!', views='get_pdf_view_uitleg', width=35)

    tab_1.img = Image(path="DGBC.png", flex=65)
    tab_1.qr = Image(path="QRCode.png", flex=35)

    tab_1.introduction_text = Text(
        "### Welkom bij de Paris Proof app! \n"
        "Met dit programma kunt u inzien wat het verbruik is kWh per vierkante meter."
        "\n"
        "Hieronder kunt u de configuratie van het pand aanpassen."
        "\n"
        "\n"
        "Beoordeel deze app door de QR-code te scannen of naar de onderstaande website te gaan: "
        "\n"
        "#### https://forms.office.com/e/xcvnjHCFBS"
    )

    tab_1.rtng = Image(path="rating.png")


    action_2 = Step('Paris Proof app', views='get_geometry_data_view', width=20)

    action_2.breedte_text = Text(
        "## Afmetingen pand\n"
    )

    # input_1 = TextField('Text field in Section 1')
    action_2.length = NumberField('Breedte', min=60, max=300, default=150, step=6, variant='slider', flex=100)
    action_2.depth = NumberField('Diepte', min=90, max=132, default=120, step=6, variant='slider', flex=100)
    # heigth = NumberField('Hoogte', min=8, max=15, default=13, step=1, variant='slider', flex=100)

    action_2.solar_panels = NumberField('Percentage panelen (op dakvlak)..', min=0, max=40, default=5, step=1, variant='slider',
                               flex=100)
    action_2.solar_split = NumberField('Verdeling panelen', min=0, max=100, default=50, step=10, variant='slider',
                               flex=100)
    # action_2.img = Image(path="img.png", flex=65)

    # solar_panels = OptionField('Selecteer de gewenste hoeveelheid panelen..',
    #                            options=
    #                                 [OptionListElement(0, '0 %'),
    #                                 OptionListElement(0.5, '0 %'),
    #                                 OptionListElement(0.10, '0 %'),
    #                                 OptionListElement(0.15, '0 %')],
    #                                 variant='radio-inline', flex=100, default=0.25)

    # set_params = SetParamsButton('Set params to some fixed value', method='set_params')
    # clear_params = SetParamsButton('Reset params', method='clear_params')



    action_3 = Step('Paris Proof app', views='get_pdf_view')
    # action_3.text_report = Text('## Report inputs')
    # action_3.user_name = TextField('Your name')
    # action_3.project_date = DateField('Choose a project date')

class Controller(ViktorController):
    label = "Parametric Building"
    parametrization = Parametrization()



    @GeometryAndDataView("Gebouw model", duration_guess=2, default_shadow=True)#, x_axis_to_the_right=True)
    def get_geometry_data_view(self, params, **kwargs):
        # @GeometryView("3D building", duration_guess=1)
        # def get_geometry(self, params, **kwargs):
        facade_red = Material("Concrete", color=Color.from_hex("#E39D86"))
        facade_blue = Material("Concrete", color=Color.from_hex("#A2B9D5"))
        solar_blue = Material("Concrete", color=Color.from_hex('9C9AFD'))#"#7C7AFC"))

        params = params.action_2

        front_low = SquareBeam(
            length_x=params.length,
            length_y=12,
            length_z=6,
            material=facade_blue
        )
        n_front_low = front_low.translate([0, 12, 3])

        front_high = SquareBeam(
            length_x=params.length,
            length_y=12,
            length_z=6,
            material=facade_red
        )
        n_front_high = front_high.translate([0, 12, 9])

        back = SquareBeam(
            length_x=params.length,
            length_y=params.depth - 12,
            length_z=15,
            material=facade_blue
        )
        n_back = back.translate([0, 12 + (params.depth / 2), 7.5])

        geo_building = [
            n_front_low.rotate(90, (0, 0, 1)),
            n_front_high.rotate(90, (0, 0, 1)),
            n_back.rotate(90, (0, 0, 1))]

        sq_m = params.depth * params.length
        office_perc = 0.15
        sq_office = 0.15 * sq_m
        sq_warehouse = sq_m
        solar_perc = params.solar_panels / 100
        solar_split = params.solar_split / 100
        paris_proof = ParisProofApp(sq_office, sq_warehouse, office_perc, solar_perc, solar_split).app_run()

        solar_m2 = sq_m * solar_perc
        solar_width = (params.length - 10)
        depth = solar_m2 / solar_width
        rows = math.ceil(depth / 2)
        len_last = (depth % 2) / 2
        print(len_last)

        for i in range(rows):
            solar_panel = SquareBeam(
                length_x=solar_width,
                length_y=2,
                length_z=0.1,
                material=solar_blue
            )
            placement = 20 + (i * 2.2)
            solar_panel = solar_panel.translate([0, placement, 15.1])
            solar_panel.rotate(90, (0, 0, 1)),
            geo_building.append(solar_panel)

        solar_panel_last = SquareBeam(
            length_x=(solar_width * len_last),
            length_y=2,
            length_z=0.1,
            material=solar_blue
        )

        placement = 20 + (rows * 2.2)
        solar_panel = solar_panel_last.translate([0, placement, 15.1])
        solar_panel_last.rotate(90, (0, 0, 1)),
        geo_building.append(solar_panel)

        warehouse_ventilation = paris_proof['warehouse_ventilation']
        warehouse_cooling_factor = paris_proof['warehouse_cooling_factor']
        warehouse_heat_loss = paris_proof['warehouse_heat_loss']
        warehouse_lighting = paris_proof['warehouse_lighting']
        warehouse_own_usage = paris_proof['warehouse_own_usage']
        warehouse_total_kWh = paris_proof['warehouse_total_kWh']
        warehouse_yield_kWh = paris_proof['warehouse_yield_kWh']
        warehouse_difference_kWh = paris_proof['warehouse_difference_kWh']
        warehouse_difference_kWh_m2 = paris_proof['warehouse_difference_kWh_m2']
        warehouse_co2 = paris_proof['warehouse_co2']
        warehouse_cost = paris_proof['warehouse_cost']
        warehouse_paris_proof = paris_proof['warehouse_paris-proof']

        office_ventilation = paris_proof['office_ventilation']
        office_cooling_factor = paris_proof['office_cooling_factor']
        office_heat_loss = paris_proof['office_heat_loss']
        office_lighting = paris_proof['office_lighting']
        office_own_usage = paris_proof['office_own_usage']
        office_total_kWh = paris_proof['office_total_kWh']
        office_yield_kWh = paris_proof['office_yield_kWh']
        office_difference_kWh = paris_proof['office_difference_kWh']
        office_difference_kWh_m2 = paris_proof['office_difference_kWh_m2']
        office_co2 = paris_proof['office_co2']
        office_cost = paris_proof['office_cost']
        office_paris_proof = paris_proof['office_paris-proof']

        data = DataGroup(
            DataItem('Gebouw eigenschappen:', 'klik hier voor meer informatie', subgroup=DataGroup(
                DataItem('Breedte', params.length, suffix='m1'),
                DataItem('Diepte', params.depth, suffix='m1'),
                DataItem('Vierkante meters totaal', sq_m, suffix='m2'),
                DataItem('Kubieke meters totaal', sq_m*13, suffix='m3'),
                DataItem('Percentage kantoor', office_perc, suffix='%'),
                DataItem('Percentage hal', (1 - office_perc), suffix='%'),
                DataItem('Percentage panelen', params.solar_panels, suffix='%'),
            )),
            DataItem('Eis kantoor:', 70, suffix=' kWh/m2'),
            DataItem('Resultaat kantoor:', office_difference_kWh_m2, suffix="kWh/m2"),
            DataItem('Paris-proof label kantoor:', office_paris_proof),
            DataItem('Berekeningen kantoor:', "klik hier voor meer informatie", subgroup=DataGroup(
                DataItem('Eindverbruik per m2', office_difference_kWh_m2, suffix=' kWh/m2'),
                DataItem('Oppervlakte', sq_office, suffix='m2'),
                DataItem('Energieverbuik totaal', office_total_kWh, suffix='kWh', subgroup=DataGroup(
                    DataItem('Ventilatie', office_ventilation, suffix=' kWh'),
                    DataItem('Koellast', office_cooling_factor, suffix=' kWh'),
                    DataItem('Warmteverlies', office_heat_loss, suffix=' kWh'),
                    DataItem('Verlichting', office_lighting, suffix=' kWh'),
                    DataItem('Eigen verbruik', office_own_usage, suffix=' kWh'),
                )),
                DataItem('Teruglevering engergie', office_yield_kWh, suffix='kWh'),
                DataItem('Verschil engergie', office_difference_kWh, suffix='kWh'),
                DataItem('co2 verbruik', office_co2, suffix=' kg CO2'),
                DataItem('kosten', office_cost, suffix=' €'),
            )),

            DataItem('Eis bedrijfshal:', -25, suffix=' kWh/m2'),
            DataItem('Berekening bedrijfshal:', warehouse_difference_kWh_m2, suffix="kWh/m2"),
            DataItem('Paris-proof label bedrijfshal:', warehouse_paris_proof),
            DataItem('Berekening bedrijfshal:', "klik hier voor meer informatie", subgroup=DataGroup(
                DataItem('Eindverbruik per m2', warehouse_difference_kWh_m2, suffix=' kWh/m2'),
                DataItem('Oppervlakte', sq_warehouse, suffix='m2'),
                DataItem('Energieverbuik totaal', warehouse_total_kWh, suffix='kWh', subgroup=DataGroup(
                    DataItem('Ventilatie', warehouse_ventilation, suffix=' kWh'),
                    DataItem('Koellast', warehouse_cooling_factor, suffix=' kWh'),
                    DataItem('Warmteverlies', warehouse_heat_loss, suffix=' kWh'),
                    DataItem('Verlichting', warehouse_lighting, suffix=' kWh'),
                    DataItem('Eigen verbruik', warehouse_own_usage, suffix=' kWh'),
                )),
                DataItem('Teruglevering engergie', warehouse_yield_kWh, suffix='kWh'),
                DataItem('Verschil engergie', warehouse_difference_kWh, suffix='kWh'),
                DataItem('co2 verbruik', warehouse_co2, suffix=' kg CO2'),
                DataItem('kosten', warehouse_cost, suffix=' €'),
            )),
        )


        # return DataResult(data)
        return GeometryAndDataResult(
            geo_building,
            data
        )

    # @WebView("Wat is paris-proof?", duration_guess=1)
    # def get_web_view(self, params, **kwargs):
    #     return WebResult(url="https://www.dgbc.nl/themas/paris-proof")

    @PDFView("Wat is paris-proof?")
    def get_pdf_view_uitleg(self, params, **kwargs):
        file_path = Path(__file__).parent / 'Wat is Paris Proof.pdf'
        return PDFResult.from_path(file_path)

    # @WebView("Beoordeel deze app!", duration_guess=5)
    # def get_web_view2(self, params, **kwargs):
    #     return WebResult(url="https://forms.office.com/e/xcvnjHCFBS")

    # @PDFView("Report", duration_guess=10)
    # def starter_guide_report(self, params, **kwargs):
    #     values = params.action_3
    #     print(values)
    #
    #     components = [
    #         WordFileTag("user_name", values.user_name),
    #         WordFileTag("project_date", str(values.project_date))
    #     ]
    #
    #     # Get path to template and render word file
    #     template_path = Path(__file__).parent / "Template.docx"
    #     with open(template_path, 'rb') as template:
    #         word_file = render_word_file(template, components)
    #
    #     # Convert to PDF
    #     with word_file.open_binary() as f:
    #         pdf_file = convert_word_to_pdf(f)
    #
    #     return PDFResult(file=pdf_file)

    @PDFView("PDF Viewer", duration_guess=1)
    def get_pdf_view(self, params, **kwargs):
        file_path = Path(__file__).parent / 'Template.pdf'
        print(file_path)
        return PDFResult.from_path(file_path)

if __name__ == '__main__':
    concept = ParisProofApp(600, 5000, 0)
    for key, value in concept.app_run().items():
        print(f"{key}: {value}")
    print(concept.app_run())