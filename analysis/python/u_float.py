from math import sqrt

class u_float():
  def __init__(self,val,sigma=0):
    if type(val)==type(()):
      assert len(val)==2, "Not possible to construct u_float from tuple %r"%val
      self.val=val[0]
      self.sigma=val[1]
    else:
      self.val = val
      self.sigma = sigma

  def __add__(self,other):
    assert type(other)==type(self), "Can't add, two objects should be u_float but is %r."%(type(other))
    val = self.val+other.val
    sigma = sqrt(self.sigma**2+other.sigma**2)
    return u_float(val,sigma)
  def __iadd__(self,other):
    assert type(other)==type(self), "Can't add, two objects should be u_float but is %r."%(type(other))
    self.val = self.val+other.val
    self.sigma = sqrt(self.sigma**2+other.sigma**2)
    return self 
  def __sub__(self,other):
    assert type(other)==type(self), "Can't add, two objects should be u_float but is %r."%(type(other))

    val = self.val-other.val
    sigma = sqrt(self.sigma**2+other.sigma**2)
    return u_float(val,sigma)
  def __mul__(self,other):
    assert type(other)==int or type(other)==float or type(other)==type(self), "Can't multiply, %r is not a float, int or u_float"%type(other)
    if type(other)==type(self):
      val = self.val*other.val
      sigma = sqrt((self.sigma*other.val)**2+(self.val*other.sigma)**2)
    elif type(other)==int or type(other)==float:
      val = self.val*other
      sigma = self.sigma*other
    return u_float(val,sigma)
  def __div__(self,other):
    assert type(other)==int or type(other)==float or type(other)==type(self), "Can't multiply, %r is not a float, int or u_float"%type(other)
    if type(other)==type(self):
      val = self.val/other.val
      sigma = (1./other.val)*sqrt(self.sigma**2+((self.val*other.sigma)/other.val)**2)
    elif type(other)==int or type(other)==float:
      val = self.val/other
      sigma = self.sigma/other
    return u_float(val,sigma)

  def __str__(self):
    return str(self.val)+'+-'+str(self.sigma)