from traits.api import Property

def Alias(other_trait):
  def _alias_fget(self, name):
      return getattr(self, other_trait)
  def _alias_fset(self, name, value):
      old_value = getattr(self, other_trait)
      setattr(self, other_trait, value)
      self.trait_property_changed(name, old_value, value)
  def _alias_fdel(self, name):
      delattr(self, other_trait)
  return Property(fget=_alias_fget, fset=_alias_fset, fdel=_alias_fdel)
