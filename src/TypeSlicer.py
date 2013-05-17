"""
    This file is part of SEA.

    SEA is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SEA is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SEA.  If not, see <http://www.gnu.org/licenses/>.

    Copyright 2013 by neuromancer
"""

#foldr = lambda l,f,e: reduce(f, l, e)
concatSet = lambda l: reduce(set.union, l, set())
concatList = lambda l: reduce(lambda a,b: a+b, l, [])

from core import *

def typeLocs(ins, callstack, tlocs):
  
  def detectStackPtr(loc, sloc):
    
    if loc.name in ["esp","ebp"] and \
       ins.instruction == "call" and ins.called_function == None:
      
      einfo = dict()
      einfo["source.name"] = hex(callstack.currentCall())
      einfo["source.index"] = callstack.currentCounter()
      sloc.discard(loc)
      sloc.add(Type("SPtr32", loc.index, einfo))
  
  def detectHeapPtr(loc, sloc):
    #print loc.name
    if loc.name in ["eax"] and \
       ins.instruction == "call" and ins.called_function == "malloc":
     
      #assert(0)
      einfo = dict()
      einfo["source.name"] = ins.address
      einfo["source.index"] = ins.getCounter()
      sloc.discard(loc)
      sloc.add(Type("HPtr32", loc.index, einfo))
  
  
  def detectImm(loc, sloc):
    
    if loc |iss| ImmLoc:
      sloc.discard(loc)
      sloc.add(Type("Data32", loc.index))
    
  
  for sloc in tlocs:
    
    for loc in list(sloc):
      detectImm(loc, sloc)
      detectStackPtr(loc, sloc)
      detectHeapPtr(loc, sloc)
  
def checkType(tlocs):
  pt_name = tlocs[0].name
  einfo  = tlocs[0].einfo
  
  #FIXME: improve type detection
  if (all(map(lambda pt: pt.name == pt_name, tlocs))):
    return Type(pt_name, None, einfo)
    
  assert(False)
    
  
def trackLocs(ins, tlocs, read_ops, write_ops):
  
  if len(write_ops) > 1:
    assert(0)
  else:
    write_locs = write_ops[0].getLocations()
  
  for sloc in tlocs:
    
    for (i,wloc) in enumerate(write_locs):
      if (wloc in sloc):
	sloc.discard(wloc)
	
	for op in read_ops:  
	  read_locs = op.getLocations()
	  sloc.add(read_locs[i])

def getType(inss, callstack, memory, op, initial_type):
  assert(len(inss) > 0)
  
  if (op |iss| ImmOp):
    return Type("Data32", None)
  
  if (op |iss| AddrOp):
    return Type("Ptr32", None)
  
  # code should be copied and reversed
  inss.reverse()
  
  index = callstack.index

  # we will track op
  mlocs = set(op.getLocations())
  
  tlocs = range(op.getSizeInBytes())
  for (i,loc) in enumerate(op.getLocations()):
    
    pt = Type(initial_type.name, i)
    tlocs[i] = set([loc, pt])
  
  for ins in inss:
    #print str(ins)
    
    counter = ins.getCounter()
    
    if memory.getAccess(counter) <> None:
      ins.setMemoryAccess(memory.getAccess(counter))
    
    ins_write_vars = map(lambda op: set(op.getLocations()), ins.getWriteVarOperands())
    write_locs = concatSet(ins_write_vars)
    
    ins_read_vars  = map(lambda op: set(op.getLocations()), ins.getReadVarOperands())
    read_locs  = concatSet(ins_read_vars)
    
    #for loc in mlocs:
    #  print loc, "::", loc.type, "--",
    
    #if (len(mlocs) > 0):
    #  print "\n"
    
    typeLocs(ins, callstack, tlocs)
    
    if len(write_locs.intersection(mlocs)) > 0: 
      
      trackLocs(ins, tlocs, ins.getReadOperands(), ins.getWriteOperands())
      
      
      mlocs = mlocs.difference(write_locs) 
      mlocs = read_locs.union(mlocs)
    
    callstack.prevInstruction(ins)
  
  callstack.index = index
  
  for (i,s) in enumerate(tlocs):
    #for loc in tlocs[i]:
      #print loc, "-",
    tlocs[i] = joinset(s)
    
  return checkType(tlocs)