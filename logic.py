import math

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


if __name__ == '__main__':
    concept = ParisProofApp(600, 5000, 0)
    for key, value in concept.app_run().items():
        print(f"{key}: {value}")
    print(concept.app_run())