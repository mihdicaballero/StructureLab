from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Union
import math
from mento.units import kg, m, MPa
from devtools import debug
@dataclass
class Material:
    name: str

    def get_properties(self) -> Dict[str, Any]:
        return {
            'name':self.name
        }
@dataclass
class Concrete(Material):
    f_c: float = field(default=25*MPa)
    design_code: str = field(default="ACI 318-19")
    density: float = 2500*kg/m**3

    def get_properties(self) -> Dict[str, float]:
        properties = super().get_properties()
        properties['f_c'] = self.f_c
        properties['design_code'] = self.design_code
        properties['density'] = self.density
        return properties
    
@dataclass
class Concrete_ACI_318_19(Concrete):
    _E_c: float = field(init=False)
    _f_r: float = field(init=False)
    epsilon_c: float = field(default=0.003, init=False)
    _beta_1: float = field(init=False)

    def __init__(self, name: str, f_c: float):
        super().__init__(name=name, f_c=f_c)
        self._E_c = ((self.density / (kg / m**3)) ** 1.5) * 0.043 * math.sqrt(self.f_c / MPa) * MPa
        self._f_r = 0.625 * math.sqrt(self.f_c / MPa) * MPa
        self._beta_1 = self.__beta_1()

    def get_properties(self) -> dict:
        properties = super().get_properties()       
        properties['E_c'] = self._E_c
        properties['f_r'] = self._f_r
        properties['beta_1'] = self._beta_1
        properties['epsilon_c']=self.epsilon_c
        return properties
    
    def __beta_1(self) -> float:
        # Table 22.2.2.4.3—Values of β1 for equivalent rectangular concrete stress distribution
        # Page 399
        if 17 <= self.f_c / MPa <= 28:
            return 0.85
        elif 28 < self.f_c / MPa <= 55:
            return 0.85 - 0.05 / 7 * (self.f_c / MPa - 28)
        elif self.f_c / MPa > 55:
            return 0.65
        else:
            # Handle case where f_c / MPa < 17
            return 0.85  # or another appropriate value based on your requirements
        
    @property
    def E_c(self) -> float:
        return self._E_c

    @property
    def f_r(self) -> float:
        return self._f_r
    
    @property
    def beta_1(self) -> float:
        return self._beta_1
@dataclass
class Concrete_EN_1992(Concrete):
    _E_cm: float = field(init=False)  # Secant modulus of elasticity
    _f_ck: float = field(init=False) # Characteristic concrete strength
    _f_cm: float = field(init=False) # mean compressive strength
    _f_ctm: float = field(init=False) # Mean tensile strength

    def __init__(self, name: str, f_c: float):
        super().__init__(name=name, f_c=f_c)
        self.design_code = "EN 1992"
        self._f_ck = self.f_c
        self._f_cm = self._f_ck + 8 * MPa
        self._E_cm = 22000 * (self._f_cm / (10 * MPa)) ** 0.3 * MPa       
        self._f_ctm = 0.3 * (self._f_ck / MPa) ** (2/3) * MPa

    def get_properties(self) -> dict:
        properties = super().get_properties()
        properties['E_cm'] = self._E_cm
        properties['f_ctm'] = self._f_ctm
        return properties

    def alpha_cc(self) -> float:
        # Example implementation for alpha_cc, as per Eurocode EN 1992-1-1
        return 1.0  # Typically, this value is taken as 1.0 for normal weight concrete
    
    @property
    def E_c(self) -> float:
        return self._E_cm

    @property
    def f_ck(self) -> float:
        return self._f_ck
    @property
    def f_cm(self) -> float:
        return self._f_cm
    @property
    def f_ctm(self) -> float:
        return self._f_ctm

@dataclass
class Concrete_EHE_08(Concrete):
    _E_cm: float = field(init=False)  # Secant modulus of elasticity
    _f_ck: float = field(init=False) # Characteristic concrete strength
    _f_cm: float = field(init=False) # mean compressive strength
    _f_ctm: float = field(init=False) # Mean tensile strength
    _f_ctm_fl: float = field(init=False) # Mean flexure tensile strength

    def __init__(self, name: str, f_c: float):
        super().__init__(name=name, f_c=f_c)
        self.design_code = "EHE-08"
        # Calculate _E_cm and f_ctk based on f_c
        # Formulas are based on EHE-08 specifications
        self._f_ck = self.f_c
        self._f_cm = self._f_ck+8*MPa
        self._E_cm = 8500 *(self._f_cm / MPa)**(1/3) * MPa 
        self._f_ctm = 0.3 * (self._f_ck / MPa)**(2/3) * MPa 

    def get_properties(self) -> dict:
        properties = super().get_properties()
        properties['E_cm'] = self._E_cm
        properties['f_ck'] = self._f_ck
        properties['f_cm'] = self._f_cm
        properties['f_ctm'] = self._f_ctm
        return properties

    def alpha_cc(self) -> float:
        # Example implementation for alpha_cc as per EHE-08
        return 0.85  # Example value, modify according to EHE-08 standards

# Factory function
def create_concrete(name: str, f_c: float, design_code: str) -> Union[Concrete_ACI_318_19, 
                                                                      Concrete_EN_1992, Concrete_EHE_08]:
    if design_code == "ACI 318-19":
        return Concrete_ACI_318_19(name=name, f_c=f_c)
    elif design_code == "EN 1992":
        return Concrete_EN_1992(name=name, f_c=f_c)
    elif design_code == "EHE-08":
        return Concrete_EHE_08(name=name, f_c=f_c)
    else:
        raise ValueError(f"Invalid design code: {design_code}. Options: ACI 318-19, EN 1992, EHE-08.")

@dataclass
class Steel(Material):
    _f_y: float = field(init=False)
    _density: float = field(default=7850 * kg / m**3) 

    def __init__(self, name: str, f_y: float, density: float = 7850 * kg / m**3):
        super().__init__(name)
        self._f_y = f_y
        self._density = density

@dataclass
class SteelBar(Steel):
    _E_s: float = field(default=200000*MPa)
    _epsilon_y: float = field(init=False)

    def __init__(self, name: str, f_y: float, density: float =7850 *kg/m**3):
        super().__init__(name, f_y, density)
        self._epsilon_y = self._f_y / self._E_s # 21.2.2.1 - Page 392

    def get_properties(self) -> dict:
        properties = super().get_properties()
        properties['E_s'] = self._E_s
        properties['f_y'] = self._f_y
        properties['epsilon_ty']=self._epsilon_y
        return properties

@dataclass
class SteelStrand(Steel):
    _f_u: float = field(default=1860*MPa)
    _E_s: float = field(default=190000*MPa)
    prestress_stress: float = field(default=0)

    def __init__(self, name: str, f_y: float, density: float =7850 *kg/m**3):
        super().__init__(name, f_y, density)
        self._epsilon_y = self._f_y / self._E_s


    def get_properties(self) -> dict:
        properties = super().get_properties()
        properties['E_s'] = self._E_s
        properties['f_y'] = self._f_y
        properties['f_u'] = self._f_u
        return properties

def main() -> None:
    # Test cases
    concrete=create_concrete(name="H25",f_c=25*MPa, design_code="ACI 318-19")
    debug(concrete.get_properties())
    steelbar = SteelBar(name="ADN 500",f_y=500*MPa)
    debug(steelbar.get_properties())
    steelstrand = SteelStrand(name='Y1860',f_y=1700*MPa)
    debug(steelstrand.get_properties())

if __name__ == "__main__":
    main()


