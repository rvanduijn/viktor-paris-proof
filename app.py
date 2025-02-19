from viktor import ViktorController
from viktor.parametrization import ViktorParametrization, BooleanField, TextField, Section, SetParamsButton, LineBreak, Text, \
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
from logic import ParisProofApp
# viktor-cli publish --registered-name paris-proof-app  --tag v0.2.3




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


    # @action_2.handmatig_invoeren.on_change
    # def update_visibility(self, params, **kwargs):
    #     params.action_2.kantoor_m2.visible = params.action_2.handmatig_invoeren == 'yes'
    #     params.action_2.hal_m2.visible = params.action_2.handmatig_invoeren == 'yes'
    #     return params

    action_2.length = NumberField('Breedte', min=60, max=300, default=150, step=6, variant='slider', flex=100)
    action_2.depth = NumberField('Diepte', min=90, max=132, default=120, step=6, variant='slider', flex=100)
    action_2.solar_panels = NumberField('Percentage panelen (op dakvlak)..', min=0, max=40, default=5, step=1, variant='slider', flex=100)
    action_2.solar_split = NumberField('Verdeling panelen', min=0, max=100, default=50, step=10, variant='slider', flex=100)

    action_2.handmatig_invoeren = OptionField(
        'Handmatig invoeren',
        options=[
            OptionListElement('Ja', 'yes'),
            OptionListElement('Nee', 'no')
        ],
        default='no'
    )

    action_2.handmatig_invoeren = BooleanField('Handmatig invoeren', flex=100)

    action_2.kantoor_m2 = NumberField(
        'Kantoor m2',
        min=100,
        max=10000,
        default=1800,
        flex=100
    )

    action_2.hal_m2 = NumberField(
        'Hal m2',
        min=1000,
        max=100000,
        default=18000,
        flex=100
    )

    action_3 = Step('Paris Proof app', views='get_pdf_view')


class Controller(ViktorController):
    label = "Parametric Building"
    parametrization = Parametrization()



    @GeometryAndDataView("Gebouw model", duration_guess=2, default_shadow=True, x_axis_to_right=False)#, x_axis_to_the_right=True)
    def get_geometry_data_view(self, params, **kwargs):
        # DATA
        params = params.action_2
        solar_perc = params.solar_panels / 100
        solar_split = params.solar_split / 100

        if params.handmatig_invoeren:
            sq_office = params.kantoor_m2
            sq_warehouse = params.hal_m2
            sq_m = sq_office + sq_warehouse
            office_perc = sq_office / sq_m
            length_building = sq_office / 12
            depth_building = (sq_m - sq_office) / length_building

        else:
            sq_m = params.depth * params.length
            office_perc = 0.15
            sq_office = 0.15 * sq_m
            sq_warehouse = sq_m
            length_building = params.length
            depth_building = params.depth


        paris_proof = ParisProofApp(sq_office, sq_warehouse, office_perc, solar_perc, solar_split).app_run()

        solar_m2 = sq_m * solar_perc
        solar_width = (length_building - 10)
        depth = solar_m2 / solar_width
        rows = math.ceil(depth / 2)
        len_last = (depth % 2) / 2
        print(len_last)


        # GEOMETRY
        facade_red = Material("Concrete", color=Color.from_hex("#E39D86"))
        facade_blue = Material("Concrete", color=Color.from_hex("#A2B9D5"))
        solar_blue = Material("Concrete", color=Color.from_hex('9C9AFD'))#"#7C7AFC"))


        front_low = SquareBeam(
            length_x=length_building,
            length_y=12,
            length_z=6,
            material=facade_blue
        )
        n_front_low = front_low.translate([0, 12, 3])

        front_high = SquareBeam(
            length_x=length_building,
            length_y=12,
            length_z=6,
            material=facade_red
        )
        n_front_high = front_high.translate([0, 12, 9])

        back = SquareBeam(
            length_x=length_building,
            length_y=depth_building - 12,
            length_z=15,
            material=facade_blue
        )
        n_back = back.translate([0, 12 + (depth_building / 2), 7.5])

        geo_building = [
            n_front_low.rotate(90, (0, 0, 1)),
            n_front_high.rotate(90, (0, 0, 1)),
            n_back.rotate(90, (0, 0, 1))]

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
                DataItem('Breedte', length_building, suffix='m1'),
                DataItem('Diepte', depth_building, suffix='m1'),
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