#!/usr/bin/python3

import gi

gi.require_version('WebKit2', '4.0')
gi.require_version('Gtk', '3.0')

import sys
import urllib.request #Grabbing files from internet
import urllib.error
import locale #Translations go brrr
import gettext #Translations go brrr
import getpass #Used for finding username

import os

from gi.repository import Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf
from threading import Thread
from queue import Queue, Empty


def should_load(): #Should this module be loaded?
    return True


####Application Details Header
class AppDetailsHeader(Gtk.VBox):

    def __init__(self):
        
        Gtk.Box.__init__(self)
        
        self.app_icon = Gtk.Image()
        self.app_icon.set_from_icon_name("deb", Gtk.IconSize.DND)
        
        self.app_title = Gtk.Label()
        self.app_title.set_label("APPLICATION TITLE")
        
        self.app_shortdesc = Gtk.Label()
        self.app_shortdesc.set_label("APPLICATION SHORT DESCRIPTION")
        
        self.app_source_dropdown = Gtk.ComboBox()
        #NOTE TO SELF: NEVER put this in the dropdown refreshing code - it'll cause duplicated labels
        cell = Gtk.CellRendererText()
        self.app_source_dropdown.pack_start(cell, True)
        self.app_source_dropdown.add_attribute(cell, "text", 0)
        self.app_source_dropdown.connect("changed", self.on_source_dropdown_changed)
        
        self.app_subsource_dropdown = Gtk.ComboBox()
        cell2 = Gtk.CellRendererText()
        self.app_subsource_dropdown.pack_start(cell2, True)
        self.app_subsource_dropdown.add_attribute(cell2, "text", 0)
        self.app_subsource_dropdown.connect("changed", self.on_subsource_dropdown_changed)
        
        self.app_mgmt_progress = Gtk.ProgressBar()
        
        buttonsbox = Gtk.Box()
        
        self.installapp_btn = Gtk.Button(label=("Install"))
        self.installappnosource_btn = Gtk.Button(label=("Install..."))
        self.updateapp_btn = Gtk.Button(label=("Update"))
        self.removeapp_btn = Gtk.Button(label=("Remove"))
        self.cancelapp_btn = Gtk.Button(label=("Cancel"))
        
        buttonsbox.pack_start(self.installapp_btn, False, False, 4)
        buttonsbox.pack_start(self.installappnosource_btn, False, False, 4)
        buttonsbox.pack_start(self.updateapp_btn, False, False, 4)
        buttonsbox.pack_start(self.removeapp_btn, False, False, 4)
        buttonsbox.pack_start(self.cancelapp_btn, False, False, 4)
        
        self.pack_start(self.app_icon, False, False, 4)
        self.pack_start(self.app_title, True, False, 4)
        self.pack_start(self.app_shortdesc, True, False, 4)
        self.pack_start(self.app_source_dropdown, False, False, 4)
        self.pack_start(self.app_subsource_dropdown, False, False, 4)
        self.pack_start(self.app_mgmt_progress, True, False, 4)
        self.pack_start(buttonsbox, True, False, 4)
        
        
        self.installapp_btn.connect("clicked", self.installapp_pressed)
        self.installappnosource_btn.connect("clicked", self.installappnosource_pressed)
        self.updateapp_btn.connect("clicked", self.updateapp_pressed)
        self.removeapp_btn.connect("clicked", self.removeapp_pressed)
        self.cancelapp_btn.connect("clicked", self.cancelapp_pressed)
        
        #For sources
        self.source_ids = []
        self.subsource_ids = []
        
        pass
    
    def set_icon(self, iconuri, packagetoview):
        tempdir = self.storebrain.tempdir + "/icons"
        
        #Set the icon shown on the package header
                
        desired_width = 48
        desired_height = 48
        try:
            if not iconuri.startswith("file://"):
                #Download the application icon
                if not os.path.isfile(tempdir+"/"+packagetoview):
                    urllib.request.urlretrieve(iconuri, tempdir+"/"+packagetoview)
                #Set it as the icon in the Store
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(tempdir+"/"+packagetoview)
            else:
                #Set it as the icon in the Store
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(iconuri.split('file://')[1])
        except Exception as exceptionstring:
            print("Could not retrieve icon for", packagetoview, "-", exceptionstring)
            #TODO: Change to store-missing-icon
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file("/usr/share/icons/Inspire/256/apps/feren-store.png")
        icon_pixbuf = icon_pixbuf.scale_simple(desired_width, desired_height, GdkPixbuf.InterpType.BILINEAR)
        self.app_icon.set_from_pixbuf(icon_pixbuf)
    
    def populate(self, info, currentpackage):
        self.app_title.set_label(info["realname"])
        self.app_shortdesc.set_label(info["shortdescription"])
        self.set_icon(info["iconuri"], currentpackage)
        pass #TODO
    
    def populate_sources(self, currentpackage, sourcedict):
        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)
        self.source_ids = []
        for item in sourcedict:
            iface_list_store.append([sourcedict[item]])
            self.source_ids.append(item)
            
        self.app_source_dropdown.set_model(iface_list_store)
        self.app_source_dropdown.set_active(0)
    
    def populate_subsources(self, currentpackage, subsourcedict):
        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)
        self.subsource_ids = []
        for item in subsourcedict:
            iface_list_store.append([subsourcedict[item]])
            self.subsource_ids.append(item)
            
        self.app_subsource_dropdown.set_model(iface_list_store)
        self.app_subsource_dropdown.set_active(0)
        
    def on_source_dropdown_changed(self, combobox):
        if combobox.get_active() == -1:
            return
        print("DEBUG: Source changed to", self.source_ids[combobox.get_active()])
        self.mv.current_subsource_viewed = ""
        self.mv.current_module_viewed = self.source_ids[combobox.get_active()].split(":")[0]
        self.mv.current_source_viewed = self.source_ids[combobox.get_active()].split(":")[1]
        self.storebrain.add_to_packageinfo(self.mv.current_item_viewed, self.mv.current_source_viewed)
        self.mv.packagepage_refresh(self.mv.current_item_viewed, self.mv.current_module_viewed, self.mv.current_source_viewed)
        self.populate_subsources(self.mv.current_item_viewed, self.storebrain.get_subsources(self.mv.current_source_viewed, self.mv.current_module_viewed))
        
    def on_subsource_dropdown_changed(self, combobox):
        if combobox.get_active() == -1:
            self.mv.current_subsource_viewed = ""
            return
        print("DEBUG: Sub-Source changed to", self.subsource_ids[combobox.get_active()])
        self.mv.current_subsource_viewed = self.subsource_ids[combobox.get_active()]

    def set_progress(self, value):
        self.app_mgmt_progress.set_fraction(value / 100)

    def installapp_pressed(self, gtk_widget):
        #TODO: Confirmation and whatnot, let's just get the main event working first
        subsource = self.mv.current_subsource_viewed
        bonuses = ["ublock", "nekocap"]
        self.storebrain.package_module(self.mv.current_source_viewed).install_package(self.mv.current_item_viewed, self.mv.current_source_viewed, self.mv.current_subsource_viewed, bonuses)

    def installappnosource_pressed(self, gtk_widget):
        #TODO
        pass

    def updateapp_pressed(self, gtk_widget):
        #TODO: Confirmation and whatnot, let's just get the main event working first
        self.storebrain.package_module(self.mv.current_source_viewed).update_package(self.mv.current_item_viewed, self.mv.current_source_viewed, self.mv.current_subsource_viewed)

    def removeapp_pressed(self, gtk_widget):
        source = ""
        #TODO: Confirmation and whatnot, let's just get the main event working first
        self.storebrain.package_module(self.mv.current_source_viewed).remove_package(self.mv.current_item_viewed, self.mv.current_source_viewed, self.mv.current_subsource_viewed)

    def cancelapp_pressed(self, gtk_widget):
        #TODO
        pass
        
    def update_buttons(self, status):
        #Update buttons according to status
        if status == 0: #Uninstalled
            self.installapp_btn.set_sensitive(True)
        else:
            self.installapp_btn.set_sensitive(False)
        if status == 3: #Available in disabled source
            self.installappnosource_btn.set_sensitive(True)
        else:
            self.installappnosource_btn.set_sensitive(False)
        if status == 2: #Updatable
            self.updateapp_btn.set_sensitive(True)
        else:
            self.updateapp_btn.set_sensitive(False)
        if status == 1 or status == 2: #Installed or updatable
            self.removeapp_btn.set_sensitive(True)
        else:
            self.removeapp_btn.set_sensitive(False)
        if status == 900: #Queued
            self.cancelapp_btn.set_sensitive(True)
        else:
            self.cancelapp_btn.set_sensitive(False)
        #901 - Working on item
        


####AppView
class AppMainView(Gtk.Stack):

    def __init__(self):
        Gtk.Stack.__init__(self)
        
        self.current_item_viewed = ""
        self.current_module_viewed = ""
        self.current_source_viewed = ""
        self.current_subsource_viewed = ""
        self.back_button_history = []
        
        self.gobackmode = False
        
        self.sw = Gtk.ScrolledWindow()
        self.sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        mainpage = Gtk.VBox(spacing=8)
        
        mainlabel_box = Gtk.Box()
        mainlabel = Gtk.Label(label="Application Listings:")
        mainlabel_box.pack_start(mainlabel, False, False, 0)
        
        self.appsitems = Gtk.FlowBox()
        self.appsitems.set_margin_top(4)
        self.appsitems.set_margin_bottom(4)
        #self.appsitems.set_min_children_per_line(1)
        #self.appsitems.set_max_children_per_line(1)
        self.appsitems.set_row_spacing(4)
        self.appsitems.set_homogeneous(True)
        self.appsitems.set_valign(Gtk.Align.START)
        
        themeslabel_box = Gtk.Box()
        themeslabel = Gtk.Label(label="Themes Listings:")
        themeslabel_box.pack_start(themeslabel, False, False, 0)
        
        self.themesitems = Gtk.FlowBox()
        self.themesitems.set_margin_top(4)
        self.themesitems.set_margin_bottom(4)
        #self.themesitems.set_min_children_per_line(1)
        #self.themesitems.set_max_children_per_line(1)
        self.themesitems.set_row_spacing(4)
        self.themesitems.set_homogeneous(True)
        self.themesitems.set_valign(Gtk.Align.START)
        
        websiteslabel_box = Gtk.Box()
        websiteslabel = Gtk.Label(label="Websites Listings:")
        websiteslabel_box.pack_start(websiteslabel, False, False, 0)
        
        self.websitesitems = Gtk.FlowBox()
        self.websitesitems.set_margin_top(4)
        self.websitesitems.set_margin_bottom(4)
        #self.websitesitems.set_min_children_per_line(1)
        #self.websitesitems.set_max_children_per_line(1)
        self.websitesitems.set_row_spacing(4)
        self.websitesitems.set_homogeneous(True)
        self.websitesitems.set_valign(Gtk.Align.START)
                
        mainpage.pack_start(mainlabel_box, False, True, 0)
        mainpage.pack_start(self.appsitems, False, True, 0)
        mainpage.pack_start(themeslabel_box, False, True, 0)
        mainpage.pack_start(self.themesitems, False, True, 0)
        mainpage.pack_start(websiteslabel_box, False, True, 0)
        mainpage.pack_start(self.websitesitems, False, True, 0)
        
        mainpage.set_margin_bottom(8)
        mainpage.set_margin_top(8)
        mainpage.set_margin_left(10)
        mainpage.set_margin_right(10)
        
        self.sw.add(mainpage)
        
        
        self.add_named(self.sw, "home")
        
        
        # build tasks page
        taskspage = Gtk.VBox(spacing=8)
        
        taskslabel_box = Gtk.Box()
        taskslabel = Gtk.Label(label="Currently working on these tasks:")
        taskslabel_box.pack_start(taskslabel, False, False, 0)
        
        self.tasksitems = Gtk.FlowBox()
        self.tasksitems.set_margin_top(4)
        self.tasksitems.set_margin_bottom(4)
        self.tasksitems.set_min_children_per_line(1)
        self.tasksitems.set_max_children_per_line(1)
        self.tasksitems.set_row_spacing(4)
        self.tasksitems.set_homogeneous(True)
        self.tasksitems.set_valign(Gtk.Align.START)
        
        updateslabel_box = Gtk.Box()
        updateslabel = Gtk.Label(label="Updates are available for:")
        updateslabel_box.pack_start(updateslabel, False, False, 0)
        
        self.updatesitems = Gtk.FlowBox()
        self.updatesitems.set_margin_top(4)
        self.updatesitems.set_margin_bottom(4)
        self.updatesitems.set_min_children_per_line(1)
        self.updatesitems.set_max_children_per_line(1)
        self.updatesitems.set_row_spacing(4)
        self.updatesitems.set_homogeneous(True)
        self.updatesitems.set_valign(Gtk.Align.START)
        
        installedlabel_box = Gtk.Box()
        installedlabel = Gtk.Label(label="Currently installed:")
        installedlabel_box.pack_start(installedlabel, False, False, 0)
        
        self.installeditems = Gtk.FlowBox()
        self.installeditems.set_margin_top(4)
        self.installeditems.set_margin_bottom(4)
        self.installeditems.set_min_children_per_line(1)
        self.installeditems.set_max_children_per_line(1)
        self.installeditems.set_row_spacing(4)
        self.installeditems.set_homogeneous(True)
        self.installeditems.set_valign(Gtk.Align.START)
                
        taskspage.pack_start(taskslabel_box, False, True, 0)
        taskspage.pack_start(self.tasksitems, False, True, 0)
        taskspage.pack_start(updateslabel_box, False, True, 0)
        taskspage.pack_start(self.updatesitems, False, True, 0)
        taskspage.pack_start(installedlabel_box, False, True, 0)
        taskspage.pack_start(self.installeditems, False, True, 0)
        
        # build another scrolled window widget and add our tasks view
        self.sw2 = Gtk.ScrolledWindow()
        self.sw2.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        taskspage.set_margin_bottom(8)
        taskspage.set_margin_top(8)
        taskspage.set_margin_left(10)
        taskspage.set_margin_right(10)
        
        self.sw2.add(taskspage)
        
        
        self.add_named(self.sw2, "tasks")
        
        
        
        # build search page
        searchpage = Gtk.VBox(spacing=8)
        
        self.searchbar = Gtk.Entry()
        self.searchbar.connect("changed", self.searchbar_search)
        
        self.searchresults = Gtk.FlowBox()
        self.searchresults.set_margin_top(4)
        self.searchresults.set_margin_bottom(4)
        self.searchresults.set_min_children_per_line(1)
        self.searchresults.set_max_children_per_line(1)
        self.searchresults.set_row_spacing(4)
        self.searchresults.set_homogeneous(True)
        self.searchresults.set_valign(Gtk.Align.START)
        
        searchpage.pack_start(self.searchbar, False, True, 4)
        searchpage.pack_start(self.searchresults, False, True, 4)
        
        # build another scrolled window widget and add our search view
        self.sw3 = Gtk.ScrolledWindow()
        self.sw3.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        searchpage.set_margin_bottom(8)
        searchpage.set_margin_top(8)
        searchpage.set_margin_left(10)
        searchpage.set_margin_right(10)
        
        self.sw3.add(searchpage)
        
        
        self.add_named(self.sw3, "search")
        
        
        
        # build package page
        packagepage = Gtk.VBox(spacing=8)
        
        images_box = Gtk.Box()
        self.pkgpage_images = Gtk.Label(label="Images: ")
        images_box.pack_start(self.pkgpage_images, False, False, 0)
        
        packagepage.pack_start(images_box, False, True, 0)
        
        description_box = Gtk.Box()
        self.pkgpage_description = Gtk.Label(label="Description: ")
        description_box.pack_start(self.pkgpage_description, False, False, 0)
        
        packagepage.pack_start(description_box, False, True, 0)
        
        category_box = Gtk.Box()
        self.pkgpage_category = Gtk.Label(label="Category: ")
        category_box.pack_start(self.pkgpage_category, False, False, 0)
        
        packagepage.pack_start(category_box, False, True, 0)
        
        website_box = Gtk.Box()
        self.pkgpage_website = Gtk.Label(label="Website: ")
        website_box.pack_start(self.pkgpage_website, False, False, 0)
        
        packagepage.pack_start(website_box, False, True, 0)
        
        author_box = Gtk.Box()
        self.pkgpage_author = Gtk.Label(label="Author: ")
        author_box.pack_start(self.pkgpage_author, False, False, 0)
        
        packagepage.pack_start(author_box, False, True, 0)
        
        donateurl_box = Gtk.Box()
        self.pkgpage_donateurl = Gtk.Label(label="Donate URL: ")
        donateurl_box.pack_start(self.pkgpage_donateurl, False, False, 0)
        
        packagepage.pack_start(donateurl_box, False, True, 0)
        
        bugsurl_box = Gtk.Box()
        self.pkgpage_bugsurl = Gtk.Label(label="Bugs URL: ")
        bugsurl_box.pack_start(self.pkgpage_bugsurl, False, False, 0)
        
        packagepage.pack_start(bugsurl_box, False, True, 0)
        
        tosurl_box = Gtk.Box()
        self.pkgpage_tosurl = Gtk.Label(label="TOS URL: ")
        tosurl_box.pack_start(self.pkgpage_tosurl, False, False, 0)
        
        packagepage.pack_start(tosurl_box, False, True, 0)
        
        privpolurl_box = Gtk.Box()
        self.pkgpage_privpolurl = Gtk.Label(label="Privacy Policy URL: ")
        privpolurl_box.pack_start(self.pkgpage_privpolurl, False, False, 0)
        
        packagepage.pack_start(privpolurl_box, False, True, 0)
        
        # build another scrolled window widget and add our package view
        self.sw4 = Gtk.ScrolledWindow()
        self.sw4.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        packagepage.set_margin_bottom(8)
        packagepage.set_margin_top(8)
        packagepage.set_margin_left(10)
        packagepage.set_margin_right(10)
        
        self.sw4.add(packagepage)
        
        
        self.add_named(self.sw4, "packagepage")
    
    def packagepage_steps(self, packagename):
        self.storebrain.add_to_packageinfo(packagename, self.storebrain.get_package_sourceorder(packagename)[0])
        self.AppDetailsHeader.populate_sources(packagename, self.storebrain.get_sources(packagename))
        self.set_visible_child(self.sw4)
        
    def packagepage_refresh(self, packagename, module, source):
        
        information = self.storebrain.get_item_info(packagename, module, source)
        self.populate_pkgpage(information, packagename)
        self.AppDetailsHeader.populate(information, packagename)
        self.storebrain.pkgmgmt_modules[module].pkgstorage_add(packagename, source)
        self._refresh_page(packagename, source)
    
    
    def populate_pkgpage(self, packageinfo, currentpackage):
        self.pkgpage_images.set_label("Images: " + str(packageinfo["images"]))
        self.pkgpage_description.set_label("Description: " + str(packageinfo["description"]))
        self.pkgpage_category.set_label("Category: " + str(packageinfo["category"]))
        self.pkgpage_website.set_label("Website: " + str(packageinfo["website"]))
        self.pkgpage_author.set_label("Author: " + str(packageinfo["author"]))
        self.pkgpage_donateurl.set_label("Donate URL: " + str(packageinfo["donateurl"]))
        self.pkgpage_bugsurl.set_label("Bugs URL: " + str(packageinfo["bugreporturl"]))
        self.pkgpage_tosurl.set_label("TOS URL: " + str(packageinfo["tosurl"]))
        self.pkgpage_privpolurl.set_label("Privacy Policy URL: " + str(packageinfo["privpolurl"]))
        
    def populate_mainpage(self):
        #TODO: Split into sections
        data = self.storebrain.package_name_categories
        for pkgname in data:
            btn = Gtk.Button(label=pkgname)
            btn.connect("clicked", self._btn_goto_packageview, pkgname)
            if data[pkgname].startswith("ice-"):
                self.websitesitems.insert(btn, 1)
            elif data[pkgname].startswith("themes-"):
                self.themesitems.insert(btn, 1)
            else:
                self.appsitems.insert(btn, 1)
        
    def populate_searchpage(self, searchresults):
        #Destroy the children first (no actual children were harmed in the making of this program)
        for item in self.searchresults.get_children():
            item.destroy()
        
        for item in searchresults:
            btn = Gtk.Button(label=item)
            btn.connect("clicked", self._btn_goto_packageview, item)
            self.searchresults.insert(btn, -1)
            
        self.searchresults.show_all()
        
                
    

    def toggle_back(self):
        backbtnthread = Thread(target=self._toggle_back,
                            args=())
        backbtnthread.start()
    
    def _toggle_back(self):
        GLib.idle_add(self.__toggle_back)
    
    def __toggle_back(self):
        if len(self.back_button_history) >= 2:
            self.back_btn.set_sensitive(True)
        else:
            self.back_btn.set_sensitive(False)

    def _back_action(self, data):
        #Remove from back history
        self.gobackmode = True
        self.back_btn.set_sensitive(False) #Prevent spamming
        if not self.back_button_history[-2].startswith("packagepage-"):
            self.set_visible_child_name(self.back_button_history[-2])
        else:
            self._goto_packageview(self.back_button_history[-2][12:])
        
    def add_to_back(self):
        if self.get_visible_child() == self.sw4:
            self.back_button_history.append("packagepage-" + self.current_item_viewed)
        else:
            self.back_button_history.append(self.get_visible_child_name())
        
        self.toggle_back()
        
    def remove_from_back(self):
        if len(self.back_button_history) <= 2:
            self.back_button_history = ['home']
        else:
            self.back_button_history = self.back_button_history[:-1]
        
        self.toggle_back()
        
    def _goto_page(self, page):
        self.set_visible_child(page)
        
    def _refresh_page(self, packagename, packagetype):
        self.AppDetailsHeader.update_buttons(self.storebrain.package_module(packagetype).get_status(packagename))
        
    def _goto_packageview(self, packagename):
        self.current_item_viewed = packagename
        self.packagepage_steps(packagename)

    def _btn_goto_packageview(self, btn, packagename):
        self._goto_packageview(packagename)

    def _generate_apps_list(self, category):
        pass

    def _generate_websites_list(self, category):
        pass

    def update_insite_information(self, packagename, packagetype):
        pass
            
    def packagepagestuff(self):
        pass

    def searchbar_search(self, btn):
        if self.searchbar.get_text() == "":
            self.populate_searchpage([])
        else:
            results = self.storebrain.item_search(self.searchbar.get_text())
            self.populate_searchpage(results)



####Store Window
class main(object):    
    def __init__(self, storebrain):
        self.storebrain = storebrain

        #systemstate.first_run = self._check_first_run()
        #systemstate.first_run = True

        self._start_page = 'home.html'

    def build_app_post_splashscreen(self, mainwindow, maintoolbar, mv):
        GLib.idle_add(self._build_app_post_splashscreen, mainwindow, maintoolbar, mv)
        
        
        
        mv.populate_mainpage()

    def _build_app_post_splashscreen(self, mainwindow, maintoolbar, mv):
        # build rest of window
        box_application_header = AppDetailsHeader()
        #box_application_header.set_visible(False)
        box_application_header.parent_window = self.w
        # add the box to the parent window and show
        mainwindow.pack_start(maintoolbar, False, True, 0)
        mainwindow.pack_start(box_application_header, False, True, 0)
        mainwindow.pack_end(mv, True, True, 0)
        mv.AppDetailsHeader = box_application_header
        mv.AppDetailsHeader.storebrain = self.storebrain
        mv.AppDetailsHeader.mv = mv
        self.w.show_all()

    def _build_app(self):
        # build window
        self.w = Gtk.Window()
        self.w.set_position(Gtk.WindowPosition.CENTER)
        self.w.set_title("Storium Demo - GUI Module")
        self.w.set_default_size(850, 640)
        self.w.set_size_request(850, 540)
        #self.w.set_resizable(False)

        #This allows Store to be natively recognised as an application associated with its .desktop file
        GLib.set_prgname('/usr/bin/feren-storium')
        
        back_img = Gtk.Image()
        back_img.set_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON);

        back_btn = Gtk.Button(image=back_img)
        back_btn.set_sensitive(False)
        back_btn.set_name("back-btn")
        back_btn.set_tooltip_text("Back")
        
        status_img = Gtk.Image()
        status_img.set_from_icon_name("folder-download-symbolic", Gtk.IconSize.BUTTON);
        self.status_btn = Gtk.ToggleButton(image=status_img)
        self.status_btn.set_name("status-btn")
        self.status_btn.set_always_show_image(True)
        self.status_handle_id = self.status_btn.connect("clicked", self._status_pressed)
        self.status_btn.set_tooltip_text("See tasks and updates...")
        
        search_img = Gtk.Image()
        search_img.set_from_icon_name("edit-find-symbolic", Gtk.IconSize.BUTTON);
        self.search_btn = Gtk.ToggleButton(image=search_img)
        self.search_btn.set_name("search-btn")
        self.search_handle_id = self.search_btn.connect("clicked", self._search_pressed)
        self.search_btn.set_tooltip_text("Search for applications...")
        
        mainmenu = Gio.Menu()
        mainmenu.append("Settings... (TBD)")
        mainmenu.append("Export Application Playlist... (TBD)")
        mainmenu.append("Import Application Playlist... (TBD)")
        mainmenu.append("About Feren Storium (TBD)")
        menu_btn_img = Gtk.Image()
        menu_btn_img.set_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON);
        menu_btn = Gtk.MenuButton(image=menu_btn_img)
        menu_btn.set_use_popover(False)
        menu_btn.set_menu_model(mainmenu)
        menu_btn.set_tooltip_text("More options...")
        
        self.gohome_btn = Gtk.ToggleButton(label=("Items Page"))
        self.gohome_btn.set_name("gohome-btn")
        self.gohome_handle_id = self.gohome_btn.connect("clicked", self._gohome_pressed)
        
        #For the splash screen
        mainwindowstack = Gtk.Stack()
        mainwindowstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        #Use a titlebar-toolbar approach
        mainwindow = Gtk.VBox()
        mainwindow.set_spacing(0)
        maintoolbar = Gtk.Toolbar()
        maintoolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        maintoolbarcontents = Gtk.ToolItem()
        maintoolbarcontents.set_expand(True)
        maintoolbar.insert(maintoolbarcontents, 0)
        header = Gtk.Box()
        #maintoolbarcontents.set_border_width(2)
        maintoolbarcontents.add(header)
        header.set_spacing(6)
        toolbarspacer=Gtk.Alignment()
        
        #Logo
        logoimageandbox = Gtk.Box(spacing=8)
        logotypebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        store_logoimg = Gtk.Image()
        store_logoimg.set_from_icon_name("softwarecenter", Gtk.IconSize.DND);
        
        store_logotype1 = Gtk.Label(label=("Feren Storium"))
        
        store_logotype1_box = Gtk.Box()
        store_logotype1_box.pack_start(store_logotype1, False, False, 0)
        
        logotypebox.pack_start(store_logotype1_box, False, False, 0)
        logoimageandbox.pack_start(store_logoimg, False, False, 0)
        logoimageandbox.pack_end(logotypebox, False, False, 0)
            
        header.pack_start(back_btn, False, True, 0)
        header.pack_start(logoimageandbox, False, True, 0)
        header.pack_start(toolbarspacer, True, True, 0)
        
        buttoncentering = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        buttoncenteringbtns = Gtk.Box(spacing=4)
        buttoncentering.set_center_widget(buttoncenteringbtns)
        
        buttoncenteringbtns.pack_start(self.gohome_btn, False, True, 0)
        buttoncenteringbtns.pack_start(self.status_btn, False, True, 0)
        buttoncenteringbtns.pack_start(self.search_btn, False, True, 0)
        buttoncenteringbtns.pack_start(menu_btn, False, True, 0)
        
        header.pack_end(buttoncentering, False, False, 0)
        
        mainwindowstack.add_named(mainwindow, "window")
        
        # build page container
        mv = AppMainView()
        mv.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)

        mv.back_btn = back_btn
        mv.back_signal_handler = mv.back_btn.connect("clicked", mv._back_action)
        mv.header = header
        
        mv.storebrain = self.storebrain
        mv.modulebrain = self
        
        mv.connect("notify::visible-child", self.page_changed)
        
        #handle_id is needed to block events as otherwise the button active state changes cause button press events to occur (for whatever stupid reason) which ultimately leads to a Stack Overflow as the event code retriggers the event by triggering the button press yet again looping the cycle indefinitely

        # build scrolled window widget and add our appview stack
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.w.add(mainwindowstack)
        
        self.w.connect('delete-event', self.close)

        self._window = self.w
        self.mainpage = mv

        self.w.show_all()
        
        thread = Thread(target=self.build_app_post_splashscreen,
                        args=(mainwindow, maintoolbar, mv))
        thread.daemon = True
        thread.start()

    def init(self):
        self._build_app()
        Gtk.main()

    def _gohome_pressed(self, gtk_widget):
        self.mainpage._goto_page(self.mainpage.sw)

    def _search_pressed(self, gtk_widget):
        self.mainpage._goto_page(self.mainpage.sw3)

    def _status_pressed(self, gtk_widget):
        self.mainpage._goto_page(self.mainpage.sw2)

    def close(self, p1 = None, p2 = None):
        try:
            os.file.remove(pidfile)
        except:
            pass
        Gtk.main_quit(p1, p2)

    def page_changed(self, gtk_widget, value):
        #Toggle block buttons first
        self.gohome_btn.handler_block(self.gohome_handle_id)
        self.status_btn.handler_block(self.status_handle_id)
        self.search_btn.handler_block(self.search_handle_id)
        
        #Do their toggles and then unblock
        self.gohome_btn.set_active(False)
        self.status_btn.set_active(False)
        self.search_btn.set_active(False)
        
        
        if self.mainpage.get_visible_child() == self.mainpage.sw2: # Tasks
            self.status_btn.set_active(True)
        elif self.mainpage.get_visible_child() == self.mainpage.sw3: # Search
            self.search_btn.set_active(True)
            self.mainpage.searchbar.grab_focus()
        elif self.mainpage.get_visible_child() == self.mainpage.sw4: # Package Page
            pass
        else:
            self.gohome_btn.set_active(True)
            
        #Now unblock the signals
        self.gohome_btn.handler_unblock(self.gohome_handle_id)
        self.status_btn.handler_unblock(self.status_handle_id)
        self.search_btn.handler_unblock(self.search_handle_id)
        
        self.mainpage.AppDetailsHeader.set_visible(self.mainpage.get_visible_child() == self.mainpage.sw4)
        if self.mainpage.get_visible_child() != self.mainpage.sw4:
            self.mainpage.current_item_viewed = ""
            self.mainpage.current_source_viewed = ""
        
        if len(self.mainpage.back_button_history) >= 2 and self.mainpage.gobackmode:
            if (self.mainpage.current_item_viewed == "" and self.mainpage.get_visible_child_name() == self.mainpage.back_button_history[-2]) or (self.mainpage.back_button_history[-2] == "packagepage-" + self.mainpage.current_item_viewed):
                self.mainpage.remove_from_back()
            self.mainpage.gobackmode = False
        else:
            self.mainpage.add_to_back()
        
    def set_progress(self, packagename, packagetype, value):
        if self.mainpage.current_item_viewed == packagename and self.mainpage.current_source_viewed == packagetype:
            self.mainpage.AppDetailsHeader.set_progress(value)
        
    

    def _check_first_run(self):
        pass