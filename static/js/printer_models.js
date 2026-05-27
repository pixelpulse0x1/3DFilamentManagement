let currentModelId=null;
document.addEventListener('DOMContentLoaded',function(){
    loadModels();
    document.getElementById('addModelBtn').addEventListener('click',()=>openEdit(null));
    document.getElementById('saveModelBtn').addEventListener('click',saveModel);
    document.getElementById('cancelModelBtn').addEventListener('click',closeModal);
    document.querySelectorAll('.close-modal').forEach(b=>b.addEventListener('click',closeModal));
});
function loadModels(){
    fetch('/api/printer_models').then(r=>r.json()).then(data=>{
        const tree={};
        data.forEach(m=>{if(!tree[m.brand])tree[m.brand]=[];tree[m.brand].push(m);});
        const container=document.getElementById('modelTree');
        const brands=Object.keys(tree).sort();
        if(!brands.length){container.innerHTML='<div class="empty-state"><i class="fas fa-microchip"></i><p>暂无型号数据</p></div>';return;}
        container.innerHTML='';
        brands.forEach(brand=>{
            const models=tree[brand];
            let rows='';
            models.forEach(m=>{rows+=`
                <div class="spool-row">
                    <div class="spool-detail">
                        <span class="spool-type">${m.model_name}</span>
                        <span class="spool-weight">${m.technology}</span>
                        <span>${m.bed_size}</span>
                        <span class="spool-remark">${m.remark||''}</span>
                    </div>
                    <div class="spool-actions">
                        <button class="btn btn-outline edit-m-btn" data-id="${m.id}" data-brand="${m.brand}" data-name="${m.model_name}" data-tech="${m.technology}" data-bed="${m.bed_size}" data-rm="${m.remark||''}"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-danger del-m-btn" data-id="${m.id}" data-name="${m.model_name}"><i class="fas fa-trash"></i></button>
                    </div>
                </div>`;});
            const card=document.createElement('div');card.className='brand-tree-card';
            card.innerHTML=`<div class="brand-tree-header" onclick="this.parentElement.classList.toggle('expanded')"><div class="brand-tree-info"><i class="fas fa-chevron-right brand-tree-arrow"></i><strong>${brand}</strong><span class="brand-spool-count">${models.length} 款型号</span></div></div><div class="brand-tree-body">${rows}</div>`;
            container.appendChild(card);
        });
        document.querySelectorAll('.edit-m-btn').forEach(b=>b.addEventListener('click',function(e){e.stopPropagation();openEdit(this.dataset);}));
        document.querySelectorAll('.del-m-btn').forEach(b=>b.addEventListener('click',function(e){e.stopPropagation();deleteModel(this.dataset.id,this.dataset.name);}));
    });
}
function openEdit(ds){
    currentModelId=ds?ds.id:null;
    document.getElementById('modelModalTitle').textContent=ds?'编辑型号':'添加型号';
    document.getElementById('modelBrand').value=ds?ds.brand:'';
    document.getElementById('modelName').value=ds?ds.name:'';
    document.getElementById('modelTech').value=ds?ds.tech:'FDM';
    document.getElementById('modelBedSize').value=ds?ds.bed:'';
    document.getElementById('modelRemark').value=ds?ds.rm:'';
    document.getElementById('modelModal').style.display='flex';
}
function closeModal(){document.getElementById('modelModal').style.display='none';}
function saveModel(){
    const brand=document.getElementById('modelBrand').value.trim();
    const name=document.getElementById('modelName').value.trim();
    if(!brand||!name){alert('品牌和型号不能为空');return;}
    const body=JSON.stringify({id:currentModelId,brand,model_name:name,technology:document.getElementById('modelTech').value,bed_size:document.getElementById('modelBedSize').value,remark:document.getElementById('modelRemark').value});
    fetch('/api/printer_models',{method:currentModelId?'PUT':'POST',headers:{'Content-Type':'application/json'},body})
        .then(r=>r.json()).then(d=>{if(d.status==='success'){closeModal();loadModels();}else alert(d.error||'保存失败');});
}
function deleteModel(id,name){
    if(!confirm(`确定要删除型号「${name}」吗？`))return;
    fetch('/api/printer_models/'+id,{method:'DELETE'}).then(r=>r.json()).then(d=>{if(d.status==='success')loadModels();else alert(d.error||'删除失败');});
}
