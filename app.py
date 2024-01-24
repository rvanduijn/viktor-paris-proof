from viktor import ViktorController
from viktor.parametrization import ViktorParametrization, TextField, Section, SetParamsButton, LineBreak, Text, OptionField, OptionListElement
from viktor.geometry import SquareBeam, Material
from viktor.views import GeometryView, GeometryResult, Color, DataGroup, DataItem, DataResult, DataView, GeometryAndDataView, GeometryAndDataResult
from viktor.parametrization import NumberField
import math

class ParisProofApp(object):
    def __init__(self, BVO_office, BVO_warehouse, solar_panels_percentage):
        self.BVO_office = BVO_office
        self.BVO_warehouse = BVO_warehouse
        self.sqm_total = BVO_office + BVO_warehouse
        self.GO_office = BVO_office * 0.95
        self.GO_warehouse = BVO_warehouse * 0.97

        # ventilation_factor parameters:
        self.sqm_pp = 22
        self.vent_requirements_pp = 40
        self.vent_fact_m2 = 0.25
        self.vent_operating_hours = 2000

        # cooling_factor parameters
        self.cf_watt_p_m2_office = 60
        self.cf_operating_hours_office = 800
        self.cf_COP = 1 #3

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
        self.fill_percentage_warehouse = solar_panels_percentage #0.115
        self.panel_size = 2
        self.panel_watt_peak = 420
        self.watt_to_kWh = self.panel_watt_peak * 0.8

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

    def app_run(self):
        total_vent = self.ventilation_factor()
        total_cf = self.cooling_factor(self.cf_watt_p_m2_office, self.cf_operating_hours_office, self.cf_COP)
        total_hl_office = self.heat_loss_factor(self.hl_watt_p_m2_office, self.hl_operating_hours_office, self.hl_COP)
        total_hl_warehouse = self.heat_loss_factor(self.hl_watt_p_m2_warehouse, self.hl_operating_hours_warehouse,
                                                   self.hl_COP)
        total_lighting_office = self.lighting_usage(self.lighting_watt_p_m2_office, self.lighting_operating_hours,
                                                    self.GO_office)
        total_lighting_warehouse = self.lighting_usage(self.lighting_watt_p_m2_warehouse, self.lighting_operating_hours,
                                                       self.GO_warehouse)
        total_own_usage_office = self.own_usage(self.ou_kWh_p_m2_office, self.GO_office)
        total_own_usage_warehouse = self.own_usage(self.ou_kWh_p_m2_warehouse, self.GO_warehouse)
        total_panels = self.solar_panels_yield()

        total_kWh = total_vent + total_cf + total_hl_office + total_hl_warehouse + total_lighting_office + \
               total_lighting_warehouse + total_own_usage_office + total_own_usage_warehouse - total_panels

        dict_results = {
            'BVO_office': self.BVO_office,
            'BVO_warehouse': self.BVO_warehouse,
            '': '------------------------------------- :',
            'ventilation': total_vent,
            'cooling_factor': total_cf,
            'heat_loss_office': total_hl_office,
            'heat_loss_warehouse': total_hl_warehouse,
            'lighting_office': total_lighting_office,
            'lighting_warehouse': total_lighting_warehouse,
            'own_usage_office': total_own_usage_office,
            'own_usage_warehouse': total_own_usage_warehouse,
            'yield_panels': total_panels,
            ':': '------------------------------------- ::',
            'total_kWh': total_kWh
        }

        return dict_results

class Parametrization(ViktorParametrization):
    introduction_text = Text(
        "## De Paris Proof app! \n"
        "Met dit programma kunt u inzien wat het verbruik is kWh per vierkante meter."
        "Hieronder kunt u de configuratie van het pand aanpassen."
    )

    breedte_text = Text(
        "## Afmetingen pand\n"
    )

    # input_1 = TextField('Text field in Section 1')
    length = NumberField('Breedte', min=60, max=300, default=150, step=6, variant='slider', flex=100)
    depth = NumberField('Diepte', min=90, max=132, default=120, step=6, variant='slider', flex=100)
    # heigth = NumberField('Hoogte', min=8, max=15, default=13, step=1, variant='slider', flex=100)

    solar_panels = NumberField('Percentage panelen (op dakvlak)..', min=0, max=40, default=5, step=1, variant='slider', flex=100)

    # solar_panels = OptionField('Selecteer de gewenste hoeveelheid panelen..',
    #                            options=
    #                                 [OptionListElement(0, '0 %'),
    #                                 OptionListElement(0.5, '0 %'),
    #                                 OptionListElement(0.10, '0 %'),
    #                                 OptionListElement(0.15, '0 %')],
    #                                 variant='radio-inline', flex=100, default=0.25)

    # set_params = SetParamsButton('Set params to some fixed value', method='set_params')
    # clear_params = SetParamsButton('Reset params', method='clear_params')

class Controller(ViktorController):
    label = "Parametric Building"
    parametrization = Parametrization(width=30)

    @GeometryAndDataView("Gebouw model", duration_guess=2, default_shadow=True)
    def get_geometry_data_view(self, params, **kwargs):

    # @GeometryView("3D building", duration_guess=1)
    # def get_geometry(self, params, **kwargs):
        facade_red = Material("Concrete", color=Color.from_hex("#E39D86"))
        facade_blue = Material("Concrete", color=Color.from_hex("#A2B9D5"))

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
            length_y=params.depth-12,
            length_z=15,
            material=facade_blue
        )
        n_back = back.translate([0, 12+(params.depth/2), 7.5])

        sq_m = params.depth * params.length
        sq_office = 0.15 * sq_m
        sq_warehouse = sq_m
        solar_perc = params.solar_panels / 100
        c = ParisProofApp(sq_office, sq_warehouse, solar_perc).app_run()

        v = c.get('ventilation')
        cf = c.get('cooling_factor')
        hl_o = c.get('heat_loss_office')
        hl_w = c.get('heat_loss_warehouse')
        l_o = c.get('lighting_office')
        l_w = c.get('lighting_warehouse')
        ou_o = c.get('own_usage_office')
        ou_w = c.get('own_usage_warehouse')
        yield_panels = -(c.get('yield_panels'))
        total_kWh = c.get('total_kWh')

        data = DataGroup(
            group_a=DataItem('Gebouw eigenschappen:', 'klik voor meer informatie', subgroup=DataGroup(
                DataItem('Breedte', params.length, suffix='m1'),
                DataItem('Diepte', params.depth, suffix='m1'),
                DataItem('Vierkante meters totaal', sq_office, suffix='m2'),
                DataItem('Kubieke meters totaal', sq_office, suffix='m3'),
                DataItem('Percentage kantoor', 15, suffix='%'),
                DataItem('Percentage hal', 85, suffix='%'),
                DataItem('Percentage panelen', params.solar_panels, suffix='%'),
            )),
            group_b=DataItem('Totaal verbruik:', total_kWh-yield_panels, suffix='kWh', subgroup=DataGroup(
                general=DataItem('Algemeen verbruik', v+cf, suffix='kWh', subgroup=DataGroup(
                    DataItem('Ventilatie', v, suffix=' kWh'),
                    DataItem('Koellast', cf, suffix=' kWh'),
                )),
                office=DataItem('Verbruik kantoor:', hl_o+l_o+ou_o, suffix='kWh', subgroup=DataGroup(
                    value_c=DataItem('Warmteverlies kantoor', hl_o, suffix=' kWh'),
                    value_e=DataItem('Verlichting kantoor', l_o, suffix=' kWh'),
                    value_h=DataItem('Eigen verbruik kantoor', ou_o, suffix=' kWh'),
                )),
                warehouse=DataItem('Verbruik hal', hl_w+l_w+ou_w, suffix='kWh', subgroup=DataGroup(
                    value_d=DataItem('Warmteverlies hal', hl_w, suffix=' kWh'),
                    value_f=DataItem('Verlichting hal', l_w, suffix=' kWh'),
                    value_i=DataItem('Eigen verbruik hal', ou_w, suffix=' kWh'),
                )),
            )),
            group_c=DataItem('Totaal opbrengst:', yield_panels, suffix='kWh', subgroup=DataGroup(
                DataItem('Opbrengst panelen', yield_panels, suffix=' kWh'),
            )),
            group_d=DataItem('Eindverbruik:', round((total_kWh/sq_m)*100)/100, suffix='kWh per m2', subgroup=DataGroup(
                DataItem('Totaal verbruik', hl_w+l_w+ou_w, suffix=' kWh'),
                DataItem('Totaal opbrengst', yield_panels, suffix=' kWh'),
                DataItem('Totaal eindverbruik', total_kWh, suffix=' kWh'),
                DataItem('Eindverbruik per m2', round((total_kWh/sq_m)*100)/100, suffix=' kWh/m2'),
            ))
        )

        # return DataResult(data)
        return GeometryAndDataResult([
            n_front_low.rotate(90, (0, 0, 1)),
            n_front_high.rotate(90, (0, 0, 1)),
            n_back.rotate(90, (0, 0, 1))],
            data
        )

    
    
if __name__ == '__main__':
    concept = ParisProofApp(600, 5000, 0)
    for key, value in concept.app_run().items():
        print(f"{key}: {value}")
    print(concept.app_run())