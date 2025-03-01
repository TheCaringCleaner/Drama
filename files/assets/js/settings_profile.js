function post(url) {
	var xhr = new XMLHttpRequest();
	xhr.open("POST", url, true);
	var form = new FormData()
	form.append("formkey", formkey());
	xhr.withCredentials=true;
	xhr.onload = function() {location.reload(true);};
	xhr.send(form);
};

function updatebgselection(){
	var bgselector = document.getElementById("backgroundSelector");
	const backgrounds = [
		{
			folder: "fantasy",
			backgrounds: 
			[
				"1.webp",
				"2.webp",
				"3.webp",
				"4.webp",
				"5.webp",
				"6.webp",
			]
		},
		{
			folder: "solarpunk",
			backgrounds: 
			[
				"1.webp",
				"2.webp",
				"3.webp",
				"4.webp",
				"5.webp",
				"6.webp",
				"7.webp",
				"8.webp",
				"9.webp",
				"10.webp",
				"11.webp",
				"12.webp",
				"13.webp",
				"14.webp",
				"15.webp",
				"16.webp",
				"17.webp",
				"18.webp",
				"19.webp",
			]
		},
		{
		folder: "pixelart",
		backgrounds:
		[
			"1.webp",
			"2.webp",
			"3.webp",
			"4.webp",
			"5.webp",
		]
		}
	]
		let bgContainer = document.getElementById(`bgcontainer`);
		let str = '';
		let bgsToDisplay = backgrounds[bgselector.selectedIndex].backgrounds;
		let bgsDir = backgrounds[bgselector.selectedIndex].folder;
		for (i=0; i < bgsToDisplay.length; i++) {
			let onclickPost = bgsDir + "/" + bgsToDisplay[i];
			str += `<button class="btn btn-secondary m-1 p-0" style="width:15rem; overflow: hidden;"><img loading="lazy" style="padding:0.25rem; width: 15rem" src="/assets/images/backgrounds/${bgsDir}/${bgsToDisplay[i]}" alt="${bgsToDisplay[i]}-background" onclick="post('/settings/profile?background=${onclickPost}')"></button>`;
		}
		bgContainer.innerHTML = str;
	}
	updatebgselection();