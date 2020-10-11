var tbl = document.getElementById("DatesTable");
if (tbl != null) 
{
    for (var i = 1; i < tbl.rows.length; i++) 
    {
        for (var j = 0; j < tbl.rows[i].cells.length; j++)
        {
            tbl.rows[i].cells[j].onclick = function () { getval(this); };
        }
    }
}
function getval(cel) 
{
    console.log(cel);
    document.getElementById("date").value = cel.innerHTML;
}