/* Public portfolios replace matching concept slots; concepts remain in their archive. */
function fillPortfolioSlots(concepts, portfolios) {
  const remaining = [...portfolios].sort((a,b)=>(a.display_rank??a.created)-(b.display_rank??b.created) || a.id.localeCompare(b.id));
  const slots = concepts.map(concept=>{
    const index=remaining.findIndex(work=>work.category===concept.category);
    return {slot:concept.id,work:index<0?concept:remaining.splice(index,1)[0]};
  });
  return [...slots,...remaining.map(work=>({slot:work.id,work}))];
}
if(typeof module!=='undefined')module.exports={fillPortfolioSlots};
