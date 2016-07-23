//http://jsfiddle.net/pThn6/80/
function activaTab(tab){
    $('.nav-tabs a[href="#' + tab + '"]').tab('show');
};
activaTab('overview');

//accordian code
//https://codepen.io/brenden/pen/Kwbpyj
$('.toggle').click(function(e) {
    e.preventDefault();

    var $this = $(this);

    if ($this.next().hasClass('show')) {
        $this.next().removeClass('show');
        $this.next().slideUp(350);
    } else {
        $this.parent().parent().find('li .inner').removeClass('show');
        $this.parent().parent().find('li .inner').slideUp(350);
        $this.next().toggleClass('show');
        //$this.next().slideToggle(350);
    }
});
